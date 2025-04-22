# Production Planner

This is a production planner. It takes a list of all of all materials available, what materials can be combined to produce other materials and a list of requirements of all materials to be in
the system at the end of the plan. It also has optimization targets to create plan that optimize the amount of certain numbers of resources at the end of the plan.

It frames the data as a linear programming algorithm and solves it to optimize and create a production plan.

# Requirements
python3 (3.12 but most versions should work)
scipy
numpy

#Usage

usage: main.py [-h]
               production_file inputs_file outputs_file
               commodity_importance_file time_peroid

# Example

python3 production_planner.py production.csv inputs.csv outputs.csv commodity_importance.csv 0

Output:

Result: -110799.99999999999
Output Vector: [2.e+01 1.e+04 8.e+02 1.e+05 1.e+00]
Message: Optimization terminated successfully. (HiGHS Status 7: Optimal)

Production Plan
    Produce 20.000 units of burger at burger using
        40.000 units of bread
        20.000 units of meat
    Produce 10000.000 units of money at sell_burger using
        10.000 units of burger
    Produce 800.000 units of money at sell_meat using
        80.000 units of meat
    Produce 100000.000 units of money at sell_steel using
        1.000 units of steel
    Produce 1.000 units of steel at steel using
        1.000 units of coal
        2.000 units of iron

Plan is feasible

Commodities
    bread: 0.0000 surplus - 0.0000 demanded
    burger: 0.0000 surplus - 10.0000 demanded
    coal: 1.0000 surplus - 0.0000 demanded
    iron: 0.0000 surplus - 0.0000 demanded
    meat: 0.0000 surplus - 0.0000 demanded
    money: 110800.0000 surplus - 0.0000 demanded
    steel: 0.0000 surplus - 0.0000 demanded

Final State
    bread: 40.0000 -> 0.0000
    burger: 0.0000 -> 10.0000
    coal: 2.0000 -> 1.0000
    iron: 2.0000 -> 0.0000
    meat: 100.0000 -> 0.0000
    money: 0.0000 -> 110800.0000
    steel: 0.0000 -> 0.0000

# File Formats

production_file - a csv file of all production recipes (combinations of materials that can be combined to produce other materials)

inputs_file - csv file of list of all material inputs and all constant inflows of materials

outputs_file - csv file of list of all material outputs and all constant outflows of materials

commodity_importance_file - csv file denoting the value of each material, used in creating plans that prioritize the creation or usage of certain materials (e.g. use as little money as possible,
make as many of good X as you can, ect...

time_peroid - An integer representing the time period over which the plan runs (can be left blank to ignore all inflows and outflows of materials with respect to time)

# Production File

A production_file is a csv file where each group of lines describes one recipe. A recipe is a possible way of combining commodities to produce other commodities. Each input good used to produce an output good in a given recipe consumes one line. Multiple recipes can produce the same output good.

recipe_name,output_commodity,input_commodity,input_amount,max_output
- recipe_name is the name of the recipe and must be unique. All lines related to the same recipe must have the same recipe_name and output_commodity.
- output_commodity is the name of the commodity produced by this recipe  must have the same recipe_name
- input_commodity is the name of one of the input goods that is used to produce the output_commodity
- max_output is the maximum quantity of output_commodity that this recipe can produce or -1 if unlimited quantities of output_commodity are producable by this recipe.

Example:
burger,burger,bread,2,-1
burger,burger,meat,1,-1

2 pieces of bread and 1 piece of meat can be combined to produce 1 burger. This recipe can be done unlimited times.

# Input Goods File

commodity_name,amount,is_inflow

- commodity_name is the name of a commodity that is present in the system (for use in recipes or to be stored for afterwards) before anything is done or a specification of an inflow of a certain amount of goods being added to the system over time.
- amount is the quantity of goods that is present at the start or the rate of inflow over time (e.g. 5 apples a day).
- is_inflow is 1 if this line specifies an inflow of goods or 0 if this line represents the number of goods present at start.

Example:
bread,40,0
meat,100,0

The program has 40 slices of bread and 100 pieces of meat to use at the start of the program.

# Output Goods File

commodity_name,amount,is_outflow

- commodity_name is the name of a commodity that the system must have at the end of the program.
- amount is the quantity of goods that must be present at the end of production or the amount of a certain good that must be created every single time step.
- is_outflow is 1 if this line specifies a requirement for a certain amount of goods to be present each time step or 0 if this line represents a requirement for a single flat amount of goods at the end of the plan.

Example:
burger,10,0

The plan produced must include at least 10 burgers.

# Commodity Importance File

commodity_importance_file format

commodity,value

- commodity_name is the name of a commodity to be prioritized during production planning.
- value is the cost associated with the commoditiy. The higher, the more the production planning will aim to produce plans that maximize the quantity of this good after the plan has finished. This value can be negative to direct the production planner to spend as much of this good as possible.

Example:
money,1
waste_materials,-100

Prioritize money (spend as little as possible) and get rid of all waste_materials (as much as possible)
