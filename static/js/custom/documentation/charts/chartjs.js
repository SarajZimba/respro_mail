"use strict";var KTGeneralChartJS=function(){function a(a=1,e=100){return Math.floor(Math.random()*(e-a)+a)}function e(e=1,t=100,s=10){for(var r=[],l=0;l<s;l++)r.push(a(e,t));return r}return{init:function(){Chart.defaults.font.size=13,Chart.defaults.font.family=KTUtil.getCssVariableValue("--bs-font-sans-serif"),function(){var a=document.getElementById("kt_chartjs_1"),t=KTUtil.getCssVariableValue("--bs-primary"),s=KTUtil.getCssVariableValue("--bs-danger"),r=KTUtil.getCssVariableValue("--bs-success");KTUtil.getCssVariableValue("--bs-font-sans-serif");const l={labels:["January","February","March","April","May","June","July","August","September","October","November","December"],datasets:[{label:"Dataset 1",data:e(1,100,12),backgroundColor:t,stack:"Stack 0"},{label:"Dataset 2",data:e(1,100,12),backgroundColor:s,stack:"Stack 1"},{label:"Dataset 3",data:e(1,100,12),backgroundColor:r,stack:"Stack 2"}]};new Chart(a,{type:"bar",data:l,options:{plugins:{title:{display:!1}},responsive:!0,interaction:{intersect:!1},scales:{x:{stacked:!0},y:{stacked:!0}}}})}(),function(){var a=document.getElementById("kt_chartjs_2"),t=KTUtil.getCssVariableValue("--bs-primary"),s=KTUtil.getCssVariableValue("--bs-danger");KTUtil.getCssVariableValue("--bs-success"),KTUtil.getCssVariableValue("--bs-font-sans-serif");const r={labels:["January","February","March","April","May","June","July"],datasets:[{label:"Dataset 1",data:e(1,50,7),borderColor:t,backgroundColor:"transparent"},{label:"Dataset 2",data:e(1,50,7),borderColor:s,backgroundColor:"transparent"}]};new Chart(a,{type:"line",data:r,options:{plugins:{title:{display:!1}},responsive:!0}})}(),function(){var a=document.getElementById("kt_chartjs_3"),t=KTUtil.getCssVariableValue("--bs-primary"),s=KTUtil.getCssVariableValue("--bs-danger"),r=KTUtil.getCssVariableValue("--bs-success"),l=KTUtil.getCssVariableValue("--bs-warning"),i=KTUtil.getCssVariableValue("--bs-info");const n={labels:["January","February","March","April","May"],datasets:[{label:"Dataset 1",data:e(1,100,5),backgroundColor:[t,s,r,l,i]}]};new Chart(a,{type:"pie",data:n,options:{plugins:{title:{display:!1}},responsive:!0}})}(),function(){var a=document.getElementById("kt_chartjs_4"),t=KTUtil.getCssVariableValue("--bs-primary"),s=KTUtil.getCssVariableValue("--bs-danger");KTUtil.getCssVariableValue("--bs-light-danger"),KTUtil.getCssVariableValue("--bs-font-sans-serif");const r={labels:["January","February","March","April","May","June","July","August","September","October","November","December"],datasets:[{label:"Dataset 1",data:e(50,100,12),borderColor:t,backgroundColor:"transparent",stack:"combined"},{label:"Dataset 2",data:e(1,60,12),backgroundColor:s,borderColor:s,stack:"combined",type:"bar"}]};new Chart(a,{type:"line",data:r,options:{plugins:{title:{display:!1}},responsive:!0,interaction:{intersect:!1},scales:{y:{stacked:!0}}},defaults:{font:{family:"inherit"}}})}(),function(){var a=document.getElementById("kt_chartjs_5"),t=KTUtil.getCssVariableValue("--bs-info"),s=KTUtil.getCssVariableValue("--bs-light-info"),r=KTUtil.getCssVariableValue("--bs-warning"),l=KTUtil.getCssVariableValue("--bs-light-warning"),i=KTUtil.getCssVariableValue("--bs-primary"),n=KTUtil.getCssVariableValue("--bs-light-primary");KTUtil.getCssVariableValue("--bs-font-sans-serif");const o={labels:["January","February","March","April","May","June"],datasets:[{label:"Dataset 1",data:e(20,80,6),borderColor:t,backgroundColor:s},{label:"Dataset 2",data:e(10,60,6),backgroundColor:l,borderColor:r},{label:"Dataset 3",data:e(0,80,6),backgroundColor:n,borderColor:i}]};new Chart(a,{type:"radar",data:o,options:{plugins:{title:{display:!1}},responsive:!0}})}()}}}();KTUtil.onDOMContentLoaded((function(){KTGeneralChartJS.init()}));
