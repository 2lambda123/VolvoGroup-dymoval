What is model validation?
=========================

Imagine that you are developing a super product or process. At some point, you need to test test it.
You setup all the machinery needed to test your stuff and then you run some tests.  
Depending on the tests outcome, you develop your work-product a bit more in a given direction. 
Then, at some point you test your work-product again... 
and you keep in iterating such a process over and over until you get something good to deploy. 

This is the way things are typically developed. 

However, to run tests in the *target environment*
(i.e. the *real-world environment* where your product (or service) shall be ultimately deployed) has an 
associated cost both in terms of money and in terms of time. 
Very often such cost also include personal stress.

A solution to alleviate such pain would be to run your tests in a *virtual environment* where you have a *model* 
of your *target environment*. 
If the tests of your work-product in the virtual environment show good performance, 
then you *should* get the same outcome when you test your work-product in the target environment.
Well, you *should* because the previous statement is true if, and only if, your virtual environment adequately 
represents the target environment and if it behaves similarly.

**Model validation** is the process of evaluating how good is the *model* of your *target environment*, 
i.e. it checks the similarity between your *virtual* and *target* environments through 
some validation metrics. 

More precisely, a typical validation process consists in the following steps:

#. You design a set of experiments to be carried out on the target environment.
   The set of experiments consists in defining the set of stimuli (*input*) to be given to the target environment,  

#. You run the experiments of point 1. on the target environment and you log its response. 
   The set of the *input* signals along with the response of your target environment is denoted as *measurement dataset* 
   (or, in short, just *dataset*),

#. You run exactly the *same experiment* defined in point 1. on your model and you log its response. 
   We refer to the response of your model as **simulation results**,

#. You evaluate how "close" are the simulation results and the logged response of point 2. 
   with respect to some validation metrics. 

ADD FIGURE.

If the results of step 4. are good, then you can safely keep in developing your work-product and 
test it in the virtual environment. 
Most likely things will work in the target environment as well - but it is good practice to verify that every once in a while.
Keep in mind that *"all models are wrong, but some are useful."* ;-).



However, your model is valid only within the region covered by the dataset. 
If you plan to use your model with data outside the dataset coverage region, then you have no guarantees that
your model will behave like the target environment that you want to represent.



Let's make an example showing how the steps 1-4 can be applied through a simple real-world example. 

   **Example**

   Assume that you have to develop some cool autonomous driving algorithm that shall be deployed in a car, 
   which represent your *target environment*.

   Assume that you already developed the model of a car where its input signals are *accelerator pedal position, 
   steering wheel position* and *road profile* whereas its output signals are *longitudinal speed* 
   and *lateral speed* of the vehicle. 
   Next, you want to validate your model. 

   Steps 1-4 are carried out in the following way

   #. Establish a driving route with sufficiently road slope variation. You decide to take a ride on that path by adopting a 
      nasty driving style that with sudden accelerations and abrupt steering movements.  
      
   #. You go out and drive according to plan while logging the *accelerator pedal position*, 
      the *steering wheel position* and the *road profile* time-series (input signals) along with the *longitudinal* and *lateral 
      speed* time-series of the vehicle (output signals). Such log-data represent your *dataset*. 
      *Note how input and output are separated in the dataset.*

   #. You feed your model with the dataset input signals and you observe your model output signals. 
      In other words, you feed your model with the *accelerator pedal position*, the *steering wheel position* and the *road profile* 
      time-series *logged during your ride* and you observe and store your model output 
      corresponding to the *longitudinal* and *lateral vehicle speed* into a *simulation results* data. 

   #. You compare the **logged** *longitudinal* and *lateral vehicle speed* time-series with the **simulated** 
      *longitudinal* and *lateral vehicle speed* time-series and you evaluate the results with respect to some validation metrics.

   You haven' finished yet. 
   In-fact, you should ship the coverage region of our model along with the validation results. 
   This because if you logged data only in the *accelerator pedal position* range [0,40] %, the *steering angle* 
   in the range [-2,2]° and the *road profile was flat* for all the time, then you can your model is trustworthy
   only if you use it within those bounds!  

The cost saving when using models is clear, but there is no free lunch. 
In-fact, the challenge relies in the design of good models.

Nevertheless, although the design of good models is an art that cannot be completely automated, 
we can at least validate them automatically and here is where dymoval comes into play. 
In-fact, dymoval wil not help you in developing any model at all, but it will scientifically tell you 
if your modes are good or not. 

.. note::
   A small caution on the nomenclature used: 
   we will interchangeably use the expressions *real-world system* and *target environment*. 
   This because what Control System engineers call *system* is often referred as *environment* by 
   Software Engineers.