
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


- Use WebSocket to connect the Unity, front-end interface, and back-end prediction tools. 
- Build a front-end interface to show key data such as blood glucose levels and meal size predictions. And  sync the avatar’s state with back-end data.

---
## Progress

### (1) Work Plan

-  For Front-end 
    - ~~Created or imported the virtual avatar, rigged it, and added basic logic to control its actions.~~
    - ~~Integrate AIChat system~~ into avatar
    - Add more actions for avatar
    - Debug Panel
    - Build real-time data display figure.

-  For Back-end
    - ~~Do prediction for real data~~
    - ~~Building relevence Graph~~
    - ~~Dynamic prediction~~
    - Cross Validation
    - Connect the Unity avatar to the back-end.
    - Build the blood glucose simulation module.

    

### (2) Current Issues

- ~~I found bugs in the Bayesian network prediction module. The real data scenario has error and unresonable prediction.~~
    
- ~~The Unity avatar's Animation encountered intermittent problem. And I'm looking into it.~~

- Mainly focus on front-end and communication strategy. 

    

---

## Questions

