# mypy: show_error_codes
"""Module containing everything related to validation."""

from __future__ import annotations

import matplotlib
from typing import TypedDict

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from .config import *  # noqa
from .utils import *  # noqa
from .dataset import *  # noqa
from typing import Literal
from itertools import product


class XCorrelation(TypedDict):
    # You have to manually write the type in TypedDicts docstrings
    # and you have to exclude them in the :automodule:
    """Type used to store MIMO cross-correlations.

    This data structure resembles typical Matlab *structs x* of the form
    *x.time* and *x.values*.


    Attributes
    ----------
    values: np.ndarray
        Values of the correlation tensor.
        It is a *Nxpxq* tensor, where *N* is the number of lags.
    """

    values: np.ndarray  # values collide with values() method of dict and won't be rendered
    lags: np.ndarray
    """Lags of the cross-correlation.
    It is a vector of length *N*,where *N* is the number of lags."""


def xcorr(X: np.ndarray, Y: np.ndarray) -> XCorrelation:
    """Return the normalized cross-correlation of two MIMO signals.

    If X = Y then it return the normalized auto-correlation of X.

    Parameters
    ----------
    X :
        MIMO signal realizations expressed as `Nxp` 2D array
        of `N` observations of `p` signals.
    Y :
        MIMO signal realizations expressed as `Nxq` 2D array
        of `N` observations of `q` signals.
    """
    # Reshape one-dimensional vector into"column" vectors.
    if X.ndim == 1:
        X = X.reshape(len(X), 1)
    if Y.ndim == 1:
        Y = Y.reshape(len(Y), 1)
    p = X.shape[1]
    q = Y.shape[1]

    lags = signal.correlation_lags(len(X), len(Y))  # noqa
    Rxy = np.zeros([len(lags), p, q])
    for ii in range(p):
        for jj in range(q):
            # Classic correlation definition from Probability.
            # Rxy = E[(X-mu_x)^T(Y-mu_y))]/(sigma_x*sigma_y),
            # check normalized cross-correlation for stochastic processes on Wikipedia.
            # Nevertheless, the cross-correlation is in-fact the same as E[].
            # More specifically, the cross-correlation generate a sequence
            # [E[XY(\tau=0))] E[XY(\tau=1))], ...,E[XY(\tau=N))]] and this is
            # the reason why in the computation below we use signal.correlation.
            #
            # Another way of seeing it, is that to secure that the cross-correlation
            # is always between -1 and 1, we "normalize" the observations X and Y
            # Google for "Standard score"
            #
            # At the end, for each pair (ii,jj) you have Rxy = r_{x_ii,y_jj}(\tau), therefore
            # for each (ii,jj) we compute a correlation.
            Rxy[:, ii, jj] = (
                signal.correlate(
                    (X[:, ii] - np.mean(X[:, ii])) / np.std(X[:, ii]),
                    (Y[:, jj] - np.mean(Y[:, jj])) / np.std(Y[:, jj]),
                )
                / min(len(X), len(Y))
            ).round(NUM_DECIMALS)

    xcorr_result: XCorrelation = {
        "values": Rxy,
        "lags": lags,
    }
    return xcorr_result


def rsquared(x: np.ndarray, y: np.ndarray) -> float:
    """
    Return the :math:`R^2` value of two signals.

    Signals can be MIMO.

    Parameters
    ----------
    x :
        First input signal.
    y :
        Second input signal.

    Raises
    ------
    IndexError
        If x and y don't have the same number of samples.
    """

    if x.shape != y.shape:
        raise IndexError("Arguments must have the same shape.")
    eps = x - y
    # Compute r-square fit (%)
    x_mean = np.mean(x, axis=0)
    r2 = np.round(
        (1.0 - np.linalg.norm(eps, 2) ** 2 / np.linalg.norm(x - x_mean, 2) ** 2)
        * 100,
        NUM_DECIMALS,  # noqa
    )
    return r2  # type: ignore


def _xcorr_norm_validation(
    Rxy: XCorrelation,
) -> XCorrelation:

    R = Rxy["values"]

    # MISO or SIMO case
    if R.ndim == 2:
        R = R[:, :, np.newaxis]
    # SISO case
    elif R.ndim == 1:
        R = R[:, np.newaxis, np.newaxis]
    # R cannot have dimension greater than 3
    elif R.ndim > 3:
        raise IndexError(
            "The correlation tensor must be a *3D np.ndarray* where "
            "the first dimension size is equal to the number of observartions 'N', "
            "the second dimension size is equal to the number of inputs 'p' "
            "and the third dimension size is equal to the number of outputs 'q.'"
        )

    Rxy["values"] = R

    return Rxy


def acorr_norm(
    Rxx: XCorrelation,
    l_norm: float | Literal["fro", "nuc"] | None = np.inf,
    matrix_norm: float | Literal["fro", "nuc"] | None = 2,
) -> float:
    r"""Return the norm of the auto-correlation tensor.

    It first compute the *l*-norm of each component
    :math:`(r_{i,j}(\\tau)) \in R(\\tau), i=1,\\dots p, j=1,\\dots,q`,
    where :math:`R(\\tau)` is the input tensor.
    Then, it computes the matrix-norm of the resulting matrix :math:`\\hat R`.


    Note
    ----
    Given that the auto-correlation of the same components for lags = 0
    is always 1 or -1, then the validation metrics could be jeopardized,
    especially if the l-inf norm is used.
    Therefore, the diagonal entries of the sampled auto-correlation matrix
    for lags = 0 is set to 0.0


    Parameters
    ----------
    R :
        Auto-correlation input tensor.
    l_norm :
        Type of *l*-norm.
        This parameter is passed to *numpy.linalg.norm()* method.
    matrix_norm :
        Type of matrx norm with respect to *l*-normed covariance matrix.
        This parameter is passed to *numpy.linalg.norm()* method.
    """
    Rxx = deepcopy(_xcorr_norm_validation(Rxx))

    # Auto-correlation for lags = 0 of the same component is 1 or -1
    # therefore may jeopardize the results, especially if the l-inf norm
    # is used.
    lags0_idx = np.nonzero(Rxx["lags"] == 0)[0][0]
    np.fill_diagonal(Rxx["values"][lags0_idx, :, :], 0.0)

    R_norm = xcorr_norm(Rxx, l_norm, matrix_norm)

    return R_norm


def xcorr_norm(
    Rxy: XCorrelation,
    l_norm: float | Literal["fro", "nuc"] | None = np.inf,
    matrix_norm: float | Literal["fro", "nuc"] | None = 2,
) -> float:
    r"""Return the norm of the cross-correlation tensor.

    It first compute the *l*-norm of each component
    :math:`(r_{i,j}(\\tau)) \in R(\\tau), i=1,\\dots p, j=1,\\dots,q`,
    where :math:`R(\\tau)` is the input tensor.
    Then, it computes the matrix-norm of the resulting matrix :math:`\\hat R`.

    Parameters
    ----------
    R :
        Cross-correlation input tensor.
    l_norm :
        Type of *l*-norm.
        This parameter is passed to *numpy.linalg.norm()* method.
    matrix_norm :
        Type of matrx norm with respect to *l*-normed covariance matrix.
        This parameter is passed to *numpy.linalg.norm()* method.
    """

    Rxy = _xcorr_norm_validation(Rxy)

    R = Rxy["values"]
    nrows = R.shape[1]
    ncols = R.shape[2]

    R_matrix = np.zeros((nrows, ncols))
    for ii in range(nrows):
        for jj in range(ncols):
            # R_matrix[ii, jj] = np.linalg.norm(R[:, ii, jj], l_norm) / len(
            #    R[:, ii, jj]
            # )
            R_matrix[ii, jj] = np.linalg.norm(R[:, ii, jj], l_norm)

    R_norm = np.linalg.norm(R_matrix, matrix_norm).round(NUM_DECIMALS)
    return R_norm  # type: ignore


class ValidationSession:
    # TODO: Save validation session.
    """The *ValidationSession* class is used to validate models against a given dataset.

    A *ValidationSession* object is instantiated from a :ref:`Dataset` object.
    A validation session *name* shall be also provided.

    Multiple simulation results can be appended to the *ValidationSession* instance,
    but for each ValidationSession instance only a :ref:`Dataset` object is condsidered.

    If the :ref:`Dataset` object changes,
    it is recommended to create a new *ValidationSession* instance.
    """

    def __init__(self, name: str, validation_dataset: Dataset) -> None:  # noqa
        # Once you created a ValidationSession you should not change the validation dataset.
        # Create another ValidationSession with another validation dataset
        # By using the constructors, you should have no types problems because the check is done there.

        # =============================================
        # Class attributes
        # ============================================
        self.Dataset: Dataset = validation_dataset
        """The reference :ref:`Dataset` object."""

        # Simulation based
        self.name: str = name  #: The validation session name.

        self.simulations_results: pd.DataFrame = pd.DataFrame(
            index=validation_dataset.dataset.index, columns=[[], [], []]
        )  #: The appended simulation results.

        self.auto_correlation: dict[str, XCorrelation] = {}
        """The auto-correlation tensors.
        This attribute is automatically set
        and it should be considered as a *read-only* attribute."""

        self.cross_correlation: dict[str, XCorrelation] = {}
        """The cross-correlation tensors.
        This attribute is automatically set
        and it should be considered as a *read-only* attribute."""

        # Initialize validation results DataFrame.
        idx = ["r-square (%)", "Residuals Auto-corr", "Input-Res. Cross-corr"]
        self.validation_results: pd.DataFrame = pd.DataFrame(
            index=idx, columns=[]
        )
        """The validation results.
        This attribute is automatically set
        and it should be considered as a *read-only* attribute."""

    def _append_correlations_tensors(self, sim_name: str) -> None:
        # Extract dataset
        df_val = self.Dataset.dataset
        y_sim_values = self.simulations_results[sim_name].to_numpy()

        # Move everything to numpy.
        u_values = df_val["INPUT"].to_numpy()
        y_values = df_val["OUTPUT"].to_numpy()

        # Compute residuals.
        # Consider only the residuals wrt to the logged outputs
        eps = y_values - y_sim_values

        # Residuals auto-correlation
        # R, lags = xcorr(eps, eps)
        # Ree: XCorrelation = {"values": R, "lags": lags}
        self.auto_correlation[sim_name] = xcorr(eps, eps)

        # Input-residuals cross-correlation
        # R, lags = xcorr(u_values, eps)
        # Rue: XCorrelation = {"values": R, "lags": lags}
        self.cross_correlation[sim_name] = xcorr(u_values, eps)

    def _append_validation_results(
        self,
        sim_name: str,
        l_norm: float | Literal["fro", "nuc"] | None = np.inf,
        matrix_norm: float | Literal["fro", "nuc"] | None = 2,
    ) -> None:

        # Extact dataset output values
        df_val = self.Dataset.dataset
        y_values = df_val["OUTPUT"].to_numpy()

        # Simulation results
        y_sim_values = self.simulations_results[sim_name].to_numpy()

        # rsquared
        r2 = rsquared(y_values, y_sim_values)
        # ||Ree[sim_name]||
        Ree = self.auto_correlation[sim_name]
        Ree_norm = acorr_norm(Ree, l_norm, matrix_norm)
        # ||Rue[sim_name]||
        Rue = self.cross_correlation[sim_name]
        Rue_norm = xcorr_norm(Rue, l_norm, matrix_norm)

        self.validation_results[sim_name] = [r2, Ree_norm, Rue_norm]

    def _sim_list_validate(self) -> None:
        if not self.simulations_names():
            raise KeyError(
                "The simulations list looks empty. "
                "Check the available simulation names with 'simulations_namess()'"
            )

    def _simulation_validation(
        self, sim_name: str, y_names: list[str], y_data: np.ndarray
    ) -> None:

        if len(y_names) != len(set(y_names)):
            raise ValueError("Signals name must be unique.")
        if (
            not self.simulations_results.empty
            and sim_name in self.simulations_names()
        ):
            raise ValueError(
                f"Simulation name '{sim_name}' already exists. \n"
                "HINT: check the loaded simulations names with"
                "'simulations_names()' method."
            )
        if len(set(y_names)) != len(
            set(self.Dataset.dataset["OUTPUT"].columns)
        ):
            raise IndexError(
                "The number of outputs of your simulation must be equal to "
                "the number of outputs in the dataset AND "
                "the name of each simulation output shall be unique."
            )
        if not isinstance(y_data, np.ndarray):
            raise ValueError(
                "The type the input signal values must be a numpy ndarray."
            )
        if len(y_names) not in y_data.shape:
            raise IndexError(
                "The number of labels and the number of signals must be the same."
            )
        if len(y_data) != len(self.Dataset.dataset["OUTPUT"].values):
            raise IndexError(
                "The length of the input signal must be equal to the length"
                "of the other signals in the Dataset."
            )

    def plot_simulations(
        self,
        # Cam be a positional or a keyword arg
        list_sims: str | list[str] | None = None,
        *,
        dataset: Literal["in", "out", "both"] | None = None,
        save_as: str | None = None,
    ) -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
        """Plot the stored simulation results.

        Possible values of the parameters describing the plot aesthetics,
        such as the *line_color_input* or the *alpha_output*,
        are the same for the corresponding *plot* function of *matplotlib*.

        See *matplotlib* docs for more information.

        Parameters
        ----------
        list_sims:
            List of simulation names.
        dataset:
            Specify whether the dataset shall be datasetped to the simulations results.

            - **in**: dataset only the input signals of the dataset.
            - **out**: dataset only the output signals of the dataset.
            - **both**: dataset both the input and the output signals of the dataset.

        save_as:
            Save the figure with a specified name.
            The figure is automatically resized with a 16:9-like aspect ratio.
            You must specify the complete *filename*, including the path.
        """

        # ================================================================
        # Validate and arange the plot setup.
        # ================================================================
        # check if the sim list is empty
        self._sim_list_validate()

        # Check the passed list of simulations is non-empty.
        # or that the passed name actually exist
        if not list_sims:
            list_sims = self.simulations_names()
        else:
            list_sims = str2list(list_sims)  # noqa
            sim_not_found = difference_lists_of_str(  # noqa
                list_sims, self.simulations_names()
            )
            if sim_not_found:
                raise KeyError(
                    f"Simulation {sim_not_found} not found. "
                    "Check the available simulations names with 'simulations_namess()'"
                )

        # Now we start
        ds_val = self.Dataset
        df_val = ds_val.dataset
        df_sim = self.simulations_results
        q = len(df_val["OUTPUT"].columns.get_level_values("names"))
        p = len(df_val["INPUT"].columns.get_level_values("names"))
        u_units = df_val["INPUT"].columns.get_level_values("units")
        y_units = df_val["OUTPUT"].columns.get_level_values("units")

        if dataset == "in" or dataset == "both":
            secondary_y = True
        else:
            secondary_y = False

        # ================================================================
        # Start the plot.
        # ================================================================
        # Arange figure
        cmap = plt.get_cmap(COLORMAP)
        if dataset == "in" or dataset == "both":
            n = max(p, q)
        else:
            n = q
        nrows, ncols = factorize(n)  # noqa

        # Plot the simulations output signals
        fig, axes = plt.subplots(nrows, ncols, sharex=True, squeeze=False)
        axes = axes.T.flat
        for ii, sim_name in enumerate(list_sims):
            # Scan simulation names.
            df_sim.loc[:, sim_name].plot(
                subplots=True,
                grid=True,
                ax=axes[0:q],
                secondary_y=secondary_y,
                color=cmap(ii),
                title="Simulations results.",
            )

        #  Plot the out dataset (if requested)
        if dataset == "out" or dataset == "both":
            df_val.loc[:, "OUTPUT"].plot(
                subplots=True,
                grid=True,
                color="gray",
                secondary_y=secondary_y,
                ax=axes[0:q],
            )

        # Shade NaN:s areas.
        ds_val._shade_nans(
            ds_val._nan_intervals,
            axes[0:q],
            list(df_val["OUTPUT"].droplevel(level="units", axis=1).columns),
            secondary_y=secondary_y,
            color="k",
        )

        # ==========================================================
        # Legends, labels, etc
        # ==========================================================

        # Set legend
        q = len(df_val["OUTPUT"].columns.get_level_values("names"))
        labels = list(df_sim.droplevel(level="units", axis=1).columns)

        # Legend for the dataset
        if dataset == "out" or dataset == "both":
            labels += product(
                [ds_val.name],
                list(df_val["OUTPUT"].columns.get_level_values("names")),
            )

        # Legend and titles
        for ii, ax in enumerate(axes[0:q]):
            new_labels = labels[ii::q]
            if secondary_y:
                handles, _ = ax.right_ax.get_legend_handles_labels()
                ax.right_ax.legend(handles, new_labels)
                ax.set_title(f"IN/OUT #{ii+1}")
            else:
                handles, _ = ax.get_legend_handles_labels()
                ax.legend(handles, new_labels)
                ax.set_title(f"OUTPUT #{ii+1}")

        # Set y-labels
        for jj, unit in enumerate(y_units):
            ylabel = f"({unit })"
            if secondary_y:
                axes[jj].right_ax.set_ylabel(ylabel)
            else:
                axes[jj].set_ylabel(ylabel)

        # Set xlabels
        xlabel = f"{df_val.index.name[0]} ({df_val.index.name[1]})"  # Time (s)
        for ii in range((nrows - 1) * ncols, nrows * ncols):
            axes[ii].set_xlabel(xlabel)

        # ==========================================================
        # INPUT signal hanling
        # ==========================================================
        if dataset == "in" or dataset == "both":
            df_val.loc[:, "INPUT"].plot(
                subplots=True,
                grid=True,
                color="gray",
                linestyle="--",
                ax=axes[0:p],
            )

            # Plot the last details: shade NaN:s areas.
            ds_val._shade_nans(
                ds_val._nan_intervals,
                axes[0:p],
                list(df_val["INPUT"].droplevel(level="units", axis=1).columns),
                color="k",
            )

            # Set legend
            u_names = list(df_val["INPUT"].columns.get_level_values("names"))
            u_labels = list(product([ds_val.name], u_names))
            for ii in range(p):
                axes[ii].legend([f"{u_labels[ii][0], u_labels[ii][1]}"])

            # Set leftover titles
            r = p - q
            if r > 0:
                for ii in range(r):
                    axes[q + ii].set_title(f"INPUT #{q+ii+1}")
            elif r < 0:
                for ii in range(-r):
                    axes[p + ii].set_title(f"OUTPUT #{p+ii+1}")

            # Set y_labels
            for ii, unit in enumerate(u_units):
                axes[ii].set_ylabel("(" + unit + ")")

            # Set grid
            for jj in range(q):
                axes[jj].grid(None, axis="y")

        # ===============================================================
        # Save and eventually return figures.
        # ===============================================================
        if save_as is not None:
            save_plot_as(fig, axes, save_as)  # noqa

        return fig, axes

    def plot_residuals(
        self,
        list_sims: str | list[str] | None = None,
        *,
        save_as: str | None = None,
    ) -> tuple[
        matplotlib.figure.Figure,
        matplotlib.axes.Axes,
        matplotlib.figure.Figure,
        matplotlib.axes.Axes,
    ]:
        """Plot the residuals.

        Parameters
        ----------
        list_sims :
            List of simulations.
            If empty, all the simulations are plotted.
        save_as:
            Save both figures with a specified name.
            It appends the suffix *_eps_eps* and *_u_eps* to the residuals
            auto-correlation and to the input-residuals cross-correlation figure,
            respectively.
            The figure is automatically resized with a 16:9 aspect ratio.
            The *filename* shall include the path.

        Raises
        ------
        KeyError
            If the requested simulation list is empty.
        """
        # Check if you have any simulation available
        self._sim_list_validate()
        if not list_sims:
            list_sims = self.simulations_names()
        else:
            list_sims = str2list(list_sims)  # noqa
            sim_not_found = difference_lists_of_str(  # noqa
                list_sims, self.simulations_names()
            )
            if sim_not_found:
                raise KeyError(
                    f"Simulation {sim_not_found} not found. "
                    "Check the available simulations names with 'simulations_namess()'"
                )
        Ree = self.auto_correlation
        Rue = self.cross_correlation

        # Get p
        k0 = list(Rue.keys())[0]
        Rue[k0]["values"][0, :, :]
        p = Rue[k0]["values"][0, :, :].shape[0]

        # Get q
        k0 = list(Ree.keys())[0]
        Ree[k0]["values"][0, :, :]
        q = Ree[k0]["values"][0, :, :].shape[0]

        # ===============================================================
        # Plot residuals auto-correlation
        # ===============================================================
        fig1, ax1 = plt.subplots(q, q, sharex=True, squeeze=False)
        plt.setp(ax1, ylim=(-1.2, 1.2))
        for sim_name in list_sims:
            for ii in range(q):
                for jj in range(q):
                    ax1[ii, jj].plot(
                        Ree[sim_name]["lags"],
                        Ree[sim_name]["values"][:, ii, jj],
                        label=sim_name,
                    )
                    ax1[ii, jj].grid(True)
                    ax1[ii, jj].set_xlabel("Lags")
                    # For the following LaTeX is needed.
                    #  ax1[ii, jj].set_title(
                    #      rf"$\hat r_{{\epsilon_{ii}\epsilon_{jj}}}$"
                    #  )
                    ax1[ii, jj].set_title(rf"r_eps{ii}eps_{jj}")
                    ax1[ii, jj].legend()
        plt.suptitle("Residuals auto-correlation")

        # ===============================================================
        # Plot input-residuals cross-correlation
        # ===============================================================
        fig2, ax2 = plt.subplots(p, q, sharex=True, squeeze=False)
        plt.setp(ax2, ylim=(-1.2, 1.2))
        for sim_name in list_sims:
            for ii in range(p):
                for jj in range(q):
                    ax2[ii, jj].plot(
                        Rue[sim_name]["lags"],
                        Rue[sim_name]["values"][:, ii, jj],
                        label=sim_name,
                    )
                    ax2[ii, jj].grid(True)
                    ax2[ii, jj].set_xlabel("Lags")
                    # For the following the user needs LaTeX.
                    # ax2[ii, jj].set_title(rf"$\hat r_{{u_{ii}\epsilon_{jj}}}$")
                    ax2[ii, jj].set_title(rf"r_u{ii}eps{jj}")
                    ax2[ii, jj].legend()
        plt.suptitle("Input-residuals cross-correlation")

        if save_as is not None:
            ax1 = ax1.flat
            # fig1.set_size_inches(q * width, q * height)
            save_plot_as(fig1, ax1, save_as + "_eps_eps")  # noqa

            ax2 = ax2.flat
            # fig2.set_size_inches(q * width, p * height)
            save_plot_as(fig2, ax2, save_as + "_u_eps")  # noqa

        return fig1, ax1, fig2, ax2

    def simulation_signals_list(self, sim_name: str | list[str]) -> list[str]:
        """
        Return the signal name list of a given simulation result.

        Parameters
        ----------
        sim_name :
            Simulation name.

        Raises
        ------
        KeyError
            If the requested simulation is not in the simulation list.
        """
        self._sim_list_validate()
        return list(self.simulations_results[sim_name].columns)

    def simulations_names(self) -> list[str]:
        """Return a list of names of the stored simulations."""
        return list(self.simulations_results.columns.levels[0])

    def clear(self) -> ValidationSession:
        """Clear all the stored simulation results."""
        vs_temp = deepcopy(self)
        sim_names = vs_temp.simulations_names()
        for x in sim_names:
            vs_temp = vs_temp.drop_simulation(x)
        return vs_temp

    def append_simulation(
        self,
        sim_name: str,
        y_names: list[str],
        y_data: np.ndarray,
        l_norm: float | Literal["fro", "nuc"] | None = np.inf,
        matrix_norm: float | Literal["fro", "nuc"] | None = 2,
    ) -> ValidationSession:
        """
        Append simulation results.

        The validation metrics are automatically computed.

        Parameters
        ----------
        sim_name :
            Simulation name.
        y_label :
            Simulation output signal names.
        y_data :
            Signal realizations expressed as `Nxq` 2D array of type *float*
            with `N` observations of `q` signals.
        l_norm:
            The *l*-norm used for computing the validation results
            for this simulation.
        matrix_norm:
            The matrix norm used for computing the validation results
            for this simulation.
        """
        vs_temp = deepcopy(self)
        # df_sim = vs_temp.simulations_results

        y_names = str2list(y_names)  # noqa
        vs_temp._simulation_validation(sim_name, y_names, y_data)

        y_units = list(
            vs_temp.Dataset.dataset["OUTPUT"].columns.get_level_values("units")
        )

        # Initialize sim df
        df_sim = pd.DataFrame(data=y_data, index=vs_temp.Dataset.dataset.index)
        multicols = list(zip([sim_name] * len(y_names), y_names, y_units))
        df_sim.columns = pd.MultiIndex.from_tuples(
            multicols, names=["sim_names", "signal_names", "units"]
        )

        # Concatenate df_sim with the current sim results
        vs_temp.simulations_results = pd.concat(
            [df_sim, vs_temp.simulations_results], axis=1
        )

        # Update residuals auto-correlation and cross-correlation attributes
        vs_temp._append_correlations_tensors(sim_name)
        vs_temp._append_validation_results(sim_name)

        return vs_temp

    def drop_simulation(self, *args: str) -> ValidationSession:
        """Drop simulation results from the validation session.


        Parameters
        ----------
        *args :
            Name of the simulations to be dropped.

        Raises
        ------
        KeyError
            If the simulations list is empty.
        ValueError
            If the simulation name is not found.
        """
        vs_temp = deepcopy(self)
        vs_temp._sim_list_validate()

        for sim_name in args:
            if sim_name not in vs_temp.simulations_names():
                raise ValueError(f"Simulation {sim_name} not found.")
            vs_temp.simulations_results = vs_temp.simulations_results.drop(
                sim_name, axis=1, level="sim_names"
            )
            vs_temp.simulations_results.columns = (
                vs_temp.simulations_results.columns.remove_unused_levels()
            )

            vs_temp.auto_correlation.pop(sim_name)
            vs_temp.cross_correlation.pop(sim_name)

            vs_temp.validation_results = vs_temp.validation_results.drop(
                sim_name, axis=1
            )

        return vs_temp
