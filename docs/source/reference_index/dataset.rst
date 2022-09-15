Dataset handling
================

Measurement datasets are a central part in model validation and therefore we designed 
the :ref:`Dataset` class that offer a number of useful methods to deal with them.

There are two ways for creating a :ref:`Dataset`.

#. Through a list of :ref:`Signals <signal>`
#. Through a specific structure pandas DataFrame


.. _signal:

Signal type
-----------

If the logged signals that you want to use as dataset are not sampled with the same sampling period, 
then you must convert them into *dymoval* :ref:`signal` objects.

A  :ref:`Dataset`  object - which is what you need at the end - can be instantiated 
through a list of :ref:`signal` objects.   

.. currentmodule:: dymoval.dataset

*Dymoval* :ref:`signal` are *typeddict* with the following keys

.. rubric:: Keys
.. autosummary::

   Signal.name
   Signal.values
   Signal.signal_unit
   Signal.sampling_period
   Signal.time_unit


.. rubric:: Functions on signals

*Dymoval* offers few function for dealing with :ref:`signal`. 
Such functions are the following

.. autosummary::

   signals_validation
   fix_sampling_periods
   plot_signals


.. _Dataset:

Dataset class
-------------
The :ref:`Dataset`  class is used to store and manipulate datasets.
Since model validation requires a datasets, this class is used also to instantiate 
objects of class :ref:`ValidationSession`.  

A Dataset class object can be instantiated in two ways

#. Through a list of dymoval :ref:`Signals<signal>`,
#. Through a pandas DataFrame with a specific structure.

See :py:meth:`~dymoval.dataset.signals_validation` 
and :py:meth:`~dymoval.dataset.dataframe_validation` functions for more information.


.. currentmodule:: dymoval.dataset

.. rubric:: Constructor
.. autosummary::

   Dataset

.. rubric:: Attributes
.. autosummary::

   Dataset.name
   Dataset.dataset
   Dataset.coverage
   Dataset.information_level

.. rubric:: Manipulation methods
.. autosummary::

   Dataset.remove_means
   Dataset.remove_offset
   Dataset.low_pass_filter
   Dataset.replace_NaNs

.. rubric:: Plotting methods
.. autosummary::

   Dataset.plot
   Dataset.plot_coverage
   Dataset.plot_amplitude_spectrum

.. rubric:: Other methods
.. autosummary::
   Dataset.get_signal_list
   Dataset.get_dataset_values
   Dataset.export_to_mat

.. rubric:: Functions over Datasets
.. autosummary::

   dataframe_validation
   compare_datasets

