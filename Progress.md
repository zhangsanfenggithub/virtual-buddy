
This project is a blood glucose management tool that integrate Unity interactive virtual avatars into Bayesian network prediction. Using meal historical data, realtime  feedback, and visual virtual avatar to link  prediction and interaction

--- 
## Introduction

Focus on blood glucose management and built two parts: the Unity Interactive Virtual  Module and the Prediction Feedback Module. 

### Unity Interactive Virtual Avatar 

This part receives back-end data, provides feedback, and makes the avatar interact with user.

- create or import the virtual avatar, rig it, and add basic animations
- build control logic so users can trigger avatar feedback. 
- connect it to the back-end so the avatar’s actions and expressions can match blood glucose data and meal prediction.

### Bayesian Network meal Prediction Module

Provide predicted data for blood glucose simulation.

- Using historical meal data build a Bayesian network model. This model predicts carb intake in two scenarios: Mock data (to test the model) and real data (using actual historical eating data). - - 
-  Give prediction result to the blood glucose simulation module .

### Blood Glucose Simulation and Controller Module 

Simulate blood glucose changes and build control, to test if our meal predictions work.

- use its built-in Default Controller
- replace default meal inputs with our predictions to make the simulation dynamic. 
    
### Front-end and Back-end Communation


- Use WebSocket(or UDP port?) to connect the Unity avatar, front-end interface, and back-end prediction tools. 
- Build a front-end interface to show key data such as blood glucose levels and meal predictions. And  sync the avatar’s state with back-end data.

---
## Progress

### (1) Completed Work

-  Created or imported the virtual avatar, rigged it, and added basic logic to control its actions.
    
-  Do prediction for two scenarios: Mock data and real data

### (2) Current Issues

- I found bugs in the Bayesian network prediction module. The real data scenario has error and unresonable prediction.
    
- The Unity avatar's Animation encountered intermittent problem. And I'm looking into it.
    

### (3) Next Steps

- Fix bugs in the Bayesian network module, improve accuracy, and make sure reasonable results;
    
- Connect the Unity avatar to the back-end.
    
-  Build the blood glucose simulation module, From now on, just Try the default config and scenario of  simglucose
    
- Custom more of the controller of simglucose 
    
- Build real-time data display figure,.
    

---

## Questions



I found that activity, calorie_level and  heart rate are seems linearly related on figure, so I kept only one of (hr_level) them to improve performance. I’m not quite sure whether this might introduce too much bias. Do I need to further validate the relationship between them, or should I just include all of them in the prediction and then compare the bias?
