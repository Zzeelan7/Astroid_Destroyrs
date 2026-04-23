import React, { useEffect } from 'react';
import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';

export default function OnboardingTour() {
  useEffect(() => {
    const onboarded = localStorage.getItem('gc_onboarded');
    if (!onboarded) {
      setTimeout(() => {
        const driverObj = driver({
          showProgress: true,
          theme: 'dark',
          steps: [
            { 
              element: 'header', 
              popover: { title: 'Welcome to GridCharge', description: 'This dashboard helps you orchestrate EV charging and V2G under grid stress.', side: "bottom", align: 'start' }
            },
            { 
              element: '.panel-gsi', 
              popover: { title: 'Grid Stress Index', description: 'Real-time GSI gauge from 0-100 indicating grid stress levels. 75+ triggers emergency protocols.', side: "right", align: 'start' }
            },
            {
              // FEAT-1: Added V2G Program Status step
              element: '.panel-v2g',
              popover: { title: 'V2G Program', description: 'Monitor registered V2G-capable vehicles and active discharge sessions contributing back to the grid.', side: "left", align: 'start' }
            },
            { 
              element: '.panel-v2g-earnings', 
              popover: { title: 'Live Earnings', description: 'Watch live compensation being accrued as vehicles discharge power back to the grid in real-time via WebSockets.', side: "top", align: 'start' }
            },
            { 
              element: '.panel-simulator', 
              popover: { title: 'Scenario Simulator', description: 'Trigger different grid scenarios (Peak Stress, Transformer Failure) to see how the system adapts automatically.', side: "left", align: 'start' }
            }
          ]
        });
        driverObj.drive();
        localStorage.setItem('gc_onboarded', 'true');
      }, 1000);
    }
  }, []);

  return null;
}
