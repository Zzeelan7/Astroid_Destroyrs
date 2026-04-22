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
          steps: [
            { element: 'header', popover: { title: 'Welcome to GridCharge', description: 'This dashboard helps you orchestrate EV charging and V2G under grid stress.', side: "bottom", align: 'start' }},
            { element: '.panel-gsi', popover: { title: 'Grid Stress Index', description: 'Real-time GSI gauge from 0-100 indicating grid stress levels.', side: "bottom", align: 'start' }},
            { element: '.panel-v2g-earnings', popover: { title: 'Live Earnings', description: 'Watch live compensation being accrued as vehicles discharge power back to the grid.', side: "top", align: 'start' }},
            { element: '.panel-simulator', popover: { title: 'Scenario Simulator', description: 'Trigger different grid scenarios to see how the system adapts.', side: "left", align: 'start' }}
          ]
        });
        driverObj.drive();
        localStorage.setItem('gc_onboarded', 'true');
      }, 1000);
    }
  }, []);

  return null;
}
