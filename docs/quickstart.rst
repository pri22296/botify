************************************************************************* 
Quickstart
*************************************************************************

=========================================================================
Tasks
=========================================================================

The input text is internally parsed to create a list of data fields and
task fields. Each task field is then evaluated by capturing data elements
using the rule specified for that task. Rule is a tuple of integers which
specify the data resolution order for a given task. Let's see an example
to understand this. From here on we will be referring to nlcalc as our example.


-------------------------------------------------------------------------
Understanding with an Example
-------------------------------------------------------------------------

Lets us assume that we need to evaluate the string `what is 2 plus 3`.
Here 2 and 3 are valid data fields and `plus` is a associated with a
registered task. The rule for plus is (-1, 1).

Internally the string is parsed to a list like [2, task -> plus , 3]. Now
the rule defined for plus is (-1, 1). Therefore the task searches for the
data field at index -1 and 1 relative to it's own index. It finds 2 and
3, adds them and returns the result. Note that the rule can contain more
elements than the arity of the operation. When sufficient number of data
elements are found using the rule, the search is stopped.

-------------------------------------------------------------------------
Defining your own Tasks
-------------------------------------------------------------------------

The Botify class provides a method add_task which can be used to register
new tasks with the system. Let's just create a bot that just prints Hello
when it sees the word bot.

.. code:: python
   
   >>> from botify import Botify, Context
   >>> my_bot = Botify()
   >>> my_bot.add_task(keywords=('bot',), context=Context(lambda: print("Hello"), 1), rule=())
   >>> result = my_bot.parse("how are you bot")
   Hello
   >>> print(result)
   ()
   
Since our task needed no parameters the rule was kept empty and also no
callbacks were passed to the Botify constructor. Context can be passed a
function and it's priority. priority can be any int or float value.
Higher the priority value, earlier the task is run. The parse method returns
a tuple of left over data fields which were not consumed by any of the tasks.
Note that if a function returns a value which is a valid data field, it is
inserted back into the parsed list.


=========================================================================
Modifiers
=========================================================================

Modifiers are keywords which triggers a particular action on one of
it's target tasks. Modifiers can be used to handle the case where there are
multiple meanings for similar sentences which is common in a natural language.
There are many actions that can be performed using modifiers.

-------------------------------------------------------------------------
Updating Rules
-------------------------------------------------------------------------

A modifier can be used to trigger a change in the rule of it's target
tasks if found. Let us see an example from nlcalc, our example project.

.. code:: python

   >>> from nlcalc import NLCalculator
   >>> my_calc = NLCalculator()
   >>> print(my_calc.calculate("5 factorial"))
   120
   >>> print(my_calc.calculate("factorial of 5"))
   120
   
This works because `of` is a registered modifier which uses
Botify.ACTION_UPDATE_RULE as it's action. By default `factorial`
corresponds to the rule (-1,) but `of` changes it to (1,). Hence
`factorial` consumes the data field next to it in the second case.
   
-------------------------------------------------------------------------
Updating Context
-------------------------------------------------------------------------

A modifier can also be used to trigger a change in the context of it's
target tasks if found. Let us again see an example.

.. code:: python

   >>> from botify import Botify, Context
   >>> my_bot = Botify()
   >>> my_bot.add_task(keywords=('bot',),
                       context=Context(lambda: print("Hello"), 1),
                       rule=())
   >>> my_bot.add_modifier(modifier='my', 
                           keywords=('bot',),
                           relative_pos=1,
                           action=Botify.ACTION_UPDATE_CONTEXT,
                           parameter=Context(lambda: print("I am your bot"), 1))
   >>> result = my_bot.parse("how are you bot")
   Hello
   >>> result = my_bot.parse("how is my bot")
   I am your bot
   
Here `my` is a registered modifier. `bot` corresponds to printing `Hello`
but `my` changes it to print `I am your bot`. Note that relative_pos can never be
0 since modifiers are never stored in the parsed list.

-------------------------------------------------------------------------
Removal of a task
-------------------------------------------------------------------------

To delete a task from the internal parse list you can use the action, 
Botify.ACTION_DELETE. It removes the task if found at `relative_pos`
and corresponds to one of the tasks in the modifiers's target tasks.