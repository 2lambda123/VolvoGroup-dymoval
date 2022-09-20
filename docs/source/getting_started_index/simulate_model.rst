Simulate your model
===================

Model validation requires model output data and therefore you have to simulate your model.
How? Well, you shall feed it with the input signals contained in the :ref:`dataset <Dataset>` that you prepared.

To extract the input signals from your :ref:`dataset <Dataset>` you can use the method :py:meth:`~dymoval.dataset.get_dataset_values` 
and then you can use them to feed your model as long as you are working in a Python environment.

TODO: Otherwise, you can export your :ref:`dataset <Dataset>` in the format you want and import it into your modeling tool. 

.. note::
    Given the popularity of Matlab, dymoval has a builtin function that exports datasets signals directly in *.mat* format. 

Once you have simulated your model then you are now ready to validate your model, and guess what? 
*Dymoval* is here for that!

.. note::
    Exporting/importing signals from/to Python to/from your modeling tool may be fairly annoying. 
    For this reason, we recommend to compile your model into an FMU and use the package *pyfmu*
    to simulate your model directly from a Python environment, so you have everything in one place.

    Independently of your modeling tool (Simulink, Dymola, GT-Power, etc), you most likely 
    have an option for compiling models into FMU:s.    
    Check the documentation of your modeling tool. 

