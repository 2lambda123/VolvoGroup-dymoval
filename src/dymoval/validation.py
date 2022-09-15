# mypy: disable_error_code = ["name-defined"]
# mypy: show_error_codes
"""Module containing everything related to validation."""


import matplotlib
from typing import TypedDict

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from .config import *  # noqa
from .utils import *  # noqa
from .dataset import *  # noqa
from typing import Optional, Union, Literal


class XCorrelation(TypedDict):
    # You have to manually write the type in TypedDicts docstrings
    # and you have to exclude them in the :automodule:
    """Type used to store MIMO cross-correlations.

    This data structure resembles typical Matlab *structs x* of the form
    *x.time* and *x.values*.
    """

    values: np.ndarray
    """Values of the correlation tensor.
    It is a *Nxpxq* tensor, where *N* is the number of lags."""

    lags: np.ndarray
    """Lags of the cross-correlation.
    It is a vector of length *N*,where *N* is the number of lags."""


def xcorr(X: np.ndarray, Y: np.ndarray) -> XCorrelation:
    """Return the cross-correlation of two MIMO signals.

    If X = Y then the auto-correlation of X is computed.

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
            Rxy[:, ii, jj] = signal.correlate(  # noqa
                (X[:, ii] - np.mean(X[:, ii])) / np.std(X[:, ii]),
                (Y[:, jj] - np.mean(Y[:, jj])) / np.std(Y[:, jj]),
            ) / min(len(X), len(Y))

    xcorr_result: XCorrelation = {
        "values": Rxy,
        "lags": lags,
    }
    return xcorr_result


def rsquared(x: np.ndarray, y: np.ndarray) -> float:
    """
    Return the :math:`R^2` value of two MIMO signals..

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
        (1.0 - np.linalg.norm(eps) ** 2 / np.linalg.norm(x - x_mean) ** 2)
        * 100,
        NUM_DECIMALS,  # noqa
    )
    return r2  # type: ignore


def xcorr_norm(
    R: XCorrelation,
    l_norm: Literal[None, 1, -1, 2, -2, "inf", "-inf", "fro"] = None,
    matrix_norm: Literal[None, 1, -1, 2, -2, "inf", "-inf", "fro"] = None,
) -> float:
    """Return the norm of the cross-correlation tensor.

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
    R = Rxy["values"]

    # MISO or SIMO case
    if R.ndim == 2:
        R = R[:, :, np.newaxis]
    # SISO case
    elif R.ndim == 1:
        R = R[:, np.newaxis, np.newaxis]
    # R must have dimension 3
    elif R.ndim > 3:
        raise IndexError(
            "The correlation tensor must be a 3D np.array where "
            "the first dimension size is equal to the number of observartions 'N', "
            "the second dimension size is equal to the number of inputs 'p' "
            "and the third dimension size is equal to the number of outputs 'q.'"
        )
    nrows = R.shape[1]
    ncols = R.shape[2]

    R_matrix = np.zeros((nrows, ncols))
    for ii in range(nrows):
        for jj in range(ncols):
            R_matrix[ii, jj] = np.linalg.norm(R[:, ii, jj], l_norm) / len(
                R[:, ii, jj]
            )
    R_norm = np.linalg.norm(R_matrix, matrix_norm)
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
            index=validation_dataset.dataset.index, columns=[[], []]
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
        l_norm: Optional[int] = None,
        matrix_norm: Optional[int] = None,
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
        Ree_norm = xcorr_norm(Ree, l_norm, matrix_norm)
        # ||Rue[sim_name]||
        Rue = self.cross_correlation[sim_name]
        Rue_norm = xcorr_norm(Rue, l_norm, matrix_norm)

        self.validation_results[sim_name] = [r2, Ree_norm, Rue_norm]

    def _simulation_validation(
        self, sim_name: str, y_labels: list[str], y_data: np.ndarray
    ) -> None:

        if len(y_labels) != len(set(y_labels)):
            raise ValueError("Signals name must be unique.")
        if (
            not self.simulations_results.empty
            and sim_name in self.get_simulations_name()
        ):
            raise ValueError(
                f"Simulation name '{sim_name}' already exists. \n"
                "HINT: check the loaded simulations names with"
                "'get_simulations_names()' method."
            )
        if len(set(y_labels)) != len(
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
        if len(y_labels) not in y_data.shape:
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
        list_sims: Optional[Union[str, list[str]]] = None,
        plot_dataset: Optional[bool] = False,
        plot_input: Optional[bool] = False,
        line_color_input: Optional[str] = "k",
        linestyle_input: Optional[str] = "-",
        alpha_input: Optional[float] = 1.0,
        line_color_output: Optional[str] = "k",
        linestyle_output: Optional[str] = "-",
        alpha_output: Optional[float] = 1.0,
        return_figure: Optional[bool] = False,
        save_figure: Optional[bool] = False,
        filename: str = "",
    ) -> Optional[
        Union[
            tuple[matplotlib.figure.Figure, matplotlib.axes.Axes],
            tuple[
                matplotlib.figure.Figure,
                matplotlib.axes.Axes,
                matplotlib.figure.Figure,
                matplotlib.axes.Axes,
            ],
        ]
    ]:
        """Plot the stored simulation results.

        Possible values of the parameters describing the plot aesthetics,
        such as the *line_color_input* or the *alpha_output*,
        are the same for the corresponding *plot* function of *matplotlib*.

        See *matplotlib* docs for more information.

        Parameters
        ----------
        list_sims:
            List of simulation names.
        plot_dataset:
            If *True* it also plot the dataset output used for comparison.
        plot_input:
            If true *True* it also plot the input signals of the dataset.
        line_color_input:
            Line color for the input signals.
        linestyle_input:
            Line style for the input signals.
        alpha_input:
            Alpha channel value for the input signals.
        line_color_output:
            Line color for the output signals.
        linestyle_output:
            Line style for the output signals.
        alpha_output:
            Alpha channel value for the output signals.
        return_figure:
            If *True* it returns the figure parameters.
        save_figure:
            If *True* it save the figure on disk.
        filename:
            If *save_figure* is *True*, then this parameter specifies
            the figure filename.
        """

        # ================================================================
        # Validate and arange the plot setup.
        # ================================================================
        if not self.get_simulations_name():
            raise KeyError(
                "The simulations list looks empty. "
                "Check the available simulations names with 'get_simulations_names()'"
            )
        if not list_sims:
            list_sims = self.get_simulations_name()
        else:
            list_sims = str2list(list_sims)  # noqa
            sim_not_found = list_belonging_check(  # noqa
                list_sims, self.get_simulations_name()
            )
            if sim_not_found:
                raise KeyError(
                    f"Simulation {sim_not_found} not found. "
                    "Check the available simulations names with 'get_simulations_names()'"
                )
        # Now we start
        df_val = self.Dataset.dataset
        df_sim = self.simulations_results
        q = len(df_val["OUTPUT"].columns)

        # ================================================================
        # Start the plot. Note how idx work as a filter to select signals
        # in a certain position in all the simulations.
        # ================================================================

        cmap = plt.get_cmap(COLORMAP)  # noqa
        nrows, ncols = factorize(q)  # noqa
        # Plot the output signals
        fig_out, axes_out = plt.subplots(
            nrows, ncols, sharex=True, squeeze=False
        )
        axes_out = axes_out.flat
        for ii, sim_name in enumerate(list_sims):
            # Scan simulation names.
            df_sim.loc[:, (sim_name, df_sim[sim_name].columns)].plot(
                subplots=True,
                grid=True,
                ax=axes_out[0:q],
                color=cmap(ii),
                title="Simulations results.",
            )
        # plot output dataset if requested
        if plot_dataset:
            df_val.loc[:, ("OUTPUT", df_val["OUTPUT"].columns)].plot(
                subplots=True,
                grid=True,
                color="k",
                ax=axes_out[0:q],
            )
        for ii in range((nrows - 1) * ncols, nrows * ncols):
            axes_out[ii].set_xlabel("Time")
        self.Dataset._shade_output_nans(
            self.Dataset.dataset,
            self.Dataset._nan_intervals,
            axes_out[0:q],
            list(df_val["OUTPUT"].columns),
            color="k",
        )
        # ===============================================================
        # Input plot handling.
        # ===============================================================
        if plot_input:

            p = len(df_val["INPUT"].columns)

            nrows, ncols = factorize(p)  # noqa
            # Plot the output signals
            fig_in, axes_in = plt.subplots(
                nrows, ncols, sharex=True, squeeze=False
            )
            axes_in = axes_in.flat
            df_val.loc[:, ("INPUT", df_val["INPUT"].columns)].plot(
                subplots=True,
                color="k",
                grid=True,
                ax=axes_in[0:p],
                title="Input.",
            )
            plt.suptitle("Inputs")

            for ii in range((nrows - 1) * ncols, nrows * ncols):
                axes_in[ii].set_xlabel("Time")
            # Shade input nans
            self.Dataset._shade_input_nans(
                self.Dataset.dataset,
                self.Dataset._nan_intervals,
                axes_in[0:p],
                list(df_val["INPUT"].columns),
                color="k",
            )
            if save_figure:
                save_plot_as(fig_in, filename + "_dataset_input")  # noqa
            if return_figure:
                return fig_in, axes_in, fig_out, axes_out
        elif save_figure:
            save_plot_as(fig_out, filename + "_simulations")  # noqa
            if return_figure:
                return fig_out, axes_out
        return None

    def plot_residuals(
        self,
        list_sims: Optional[Union[str, list[str]]] = None,
        return_figure: Optional[bool] = False,
        save_figure: Optional[bool] = False,
        filename: str = "",
    ) -> Optional[
        tuple[
            matplotlib.figure.Figure,
            matplotlib.axes.Axes,
            matplotlib.figure.Figure,
            matplotlib.axes.Axes,
        ]
    ]:
        """Plot the residuals.

        Parameters
        ----------
        list_sims :
            List of simulations.
            If empty, all the simulations are plotted.
        return_figure:
            If *True* it returns the figure parameters.
        save_figure:
            If *True* it save the figure on disk.
        filename:
            If *save_figure* is *True*, then this parameter specifies
            the figure filename.

        Raises
        ------
        KeyError
            If the simulation list is empty.
        """
        # Check if you have any simulation available
        if not self.get_simulations_name():
            raise KeyError(
                "The simulations list looks empty. "
                "Check the available simulations names with 'get_simulations_names()'"
            )
        if not list_sims:
            list_sims = self.get_simulations_name()
        else:
            list_sims = str2list(list_sims)  # noqa
            sim_not_found = list_belonging_check(  # noqa
                list_sims, self.get_simulations_name()
            )
            if sim_not_found:
                raise KeyError(
                    f"Simulation {sim_not_found} not found. "
                    "Check the available simulations names with 'get_simulations_names()'"
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
                    ax1[ii, jj].set_title(
                        f"$\hat r_{{\epsilon_{ii}\epsilon_{jj}}}$"
                    )
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
                    # TODO: Escape sequence?
                    ax2[ii, jj].set_title(f"$\hat r_{{u_{ii}\epsilon_{jj}}}$")
                    ax2[ii, jj].legend()
        plt.suptitle("Input-residuals cross-correlation")

        if save_figure:
            save_plot_as(fig1, filename + "_residuals1")  # noqa
            save_plot_as(fig1, filename + "_residuals2")  # noqa
        if return_figure:
            return fig1, ax1, fig2, ax2

        return None

    # def plot_dataset(
    #     self, **kwargs: Any
    # ) -> Optional[tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]]:
    #     """It plots the stored dataset.

    #     See XXX

    #     Parameters
    #     ----------
    #     **kwargs :
    #         Arguments to be passed to dymoval.dataset.Dataset.plot() method.
    #     """
    #     return self.Dataset.plot(**kwargs)

    def get_simulation_signals_list(
        self, sim_name: Union[str, list[str]]
    ) -> list[str]:
        """
        Return the signal name list of a given simulation result.

        Parameters
        ----------
        sim_name :
            Simulation name.

        Raises
        ------
        KeyError
            If the simulation is not in the simulation list.
        """
        if not self.get_simulations_name():
            raise KeyError(
                "The simulations list looks empty. "
                "Check the available simulation names with 'get_simulations_names()'"
            )
        return list(self.simulations_results[sim_name].columns)

    # def get_dataset(self) -> pd.DataFrame:
    #     return self.Dataset.get_dataset()

    # def getDataset_values(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    #     return self.Dataset.get_dataset_values()

    # def get_dataset_signals_list(self) -> list[tuple[str, str]]:
    #     return self.Dataset.get_signal_list()

    def get_validation_metrics(self) -> pd.DataFrame:
        """Return the validation metrics of all the stored simulation names."""
        if not self.get_simulations_name():
            raise KeyError(
                "The simulations list looks empty. "
                "Check the available simulations names with 'get_simulations_names()'"
            )
        return self.validation_results

    def get_simulations_name(self) -> list[str]:
        """Return a list of names of the stored simulations."""
        return list(self.simulations_results.columns.levels[0])

    def clear(self) -> None:
        """Clear all the stored simulation results."""
        sim_names = self.get_simulations_name()
        for x in sim_names:
            self.drop_simulation(x)

    def append_simulation(
        self,
        sim_name: str,
        y_labels: list[str],
        y_data: np.ndarray,
        l_norm: Optional[int] = None,
        matrix_norm: Optional[int] = None,
    ) -> None:
        """
        Append simulation results..

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

        y_labels = str2list(y_labels)  # noqa
        self._simulation_validation(sim_name, y_labels, y_data)
        df_sim = self.simulations_results
        new_label = pd.MultiIndex.from_product([[sim_name], y_labels])
        df_sim[new_label] = y_data
        self.simulations_results = df_sim

        # Update residuals auto-correlation and cross-correlation attributes
        self._append_correlations_tensors(sim_name)
        self._append_validation_results(sim_name, l_norm=None, matrix_norm=None)

    def drop_simulation(self, *args: str) -> None:
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
        if not self.get_simulations_name():
            raise KeyError(
                "The simulations list looks empty. "
                "Check the available simulation names with 'get_simulations_names()'"
            )
        for sim_name in args:
            if sim_name not in self.get_simulations_name():
                raise ValueError(f"Simulation {sim_name} not found.")
            self.simulations_results.drop(sim_name, axis=1, inplace=True)
            self.simulations_results.columns = (
                self.simulations_results.columns.remove_unused_levels()
            )

            self.auto_correlation.pop(sim_name)
            self.cross_correlation.pop(sim_name)

            self.validation_results.drop(sim_name, axis=1, inplace=True)
