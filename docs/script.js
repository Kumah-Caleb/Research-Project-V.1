const studentForm = document.getElementById("student-form");
const predictBtn = document.getElementById("predict-btn");
const predictionResult = document.getElementById("prediction-result");

// Get input elements
const attendanceInput = document.getElementById("attendance");
const attendanceMaxInput = document.getElementById("attendance-max");
const assignmentsInput = document.getElementById("assignments");
const assignmentsMaxInput = document.getElementById("assignments-max");
const engagementInput = document.getElementById("engagement");
const engagementMaxInput = document.getElementById("engagement-max");

// Get progress bar elements
const attendanceBar = document.getElementById("attendance-bar");
const assignmentsBar = document.getElementById("assignments-bar");
const engagementBar = document.getElementById("engagement-bar");

// Get value display elements
const attendanceValue = document.getElementById("attendance-value");
const assignmentsValue = document.getElementById("assignments-value");
const engagementValue = document.getElementById("engagement-value");
const overallScore = document.getElementById("overall-score");

// Quick preset templates
const presets = {
  semester: {
    attendance: { max: 100 },
    assignments: { max: 50 },
    engagement: { max: 30 },
  },
  quarter: {
    attendance: { max: 60 },
    assignments: { max: 30 },
    engagement: { max: 20 },
  },
  module: {
    attendance: { max: 40 },
    assignments: { max: 20 },
    engagement: { max: 15 },
  },
  weekly: {
    attendance: { max: 5 },
    assignments: { max: 10 },
    engagement: { max: 8 },
  },
};

// Calculate percentage from value and max
function calculatePercentage(value, max) {
  if (!max || max <= 0) return 0;
  return Math.min((value / max) * 100, 100);
}

// Update progress bars and values in real-time
function updateProgressBars() {
  // Get values
  const attendanceVal = parseFloat(attendanceInput.value) || 0;
  const attendanceMax = parseFloat(attendanceMaxInput.value) || 1;
  const assignmentsVal = parseFloat(assignmentsInput.value) || 0;
  const assignmentsMax = parseFloat(assignmentsMaxInput.value) || 1;
  const engagementVal = parseFloat(engagementInput.value) || 0;
  const engagementMax = parseFloat(engagementMaxInput.value) || 1;

  // Calculate percentages
  const attendancePercent = calculatePercentage(attendanceVal, attendanceMax);
  const assignmentsPercent = calculatePercentage(
    assignmentsVal,
    assignmentsMax
  );
  const engagementPercent = calculatePercentage(engagementVal, engagementMax);

  // Update bars
  attendanceBar.style.width = attendancePercent + "%";
  attendanceBar.textContent = Math.round(attendancePercent) + "%";

  assignmentsBar.style.width = assignmentsPercent + "%";
  assignmentsBar.textContent = Math.round(assignmentsPercent) + "%";

  engagementBar.style.width = engagementPercent + "%";
  engagementBar.textContent = Math.round(engagementPercent) + "%";

  // Update value displays
  attendanceValue.textContent = `${attendanceVal}/${attendanceMax}`;
  assignmentsValue.textContent = `${assignmentsVal}/${assignmentsMax}`;
  engagementValue.textContent = `${engagementVal}/${engagementMax}`;

  // Calculate and update overall average
  const overallAvg =
    (attendancePercent + assignmentsPercent + engagementPercent) / 3;
  overallScore.querySelector(".score-value").textContent =
    Math.round(overallAvg) + "%";

  // Color code the bars
  updateBarColor(attendanceBar, attendancePercent);
  updateBarColor(assignmentsBar, assignmentsPercent);
  updateBarColor(engagementBar, engagementPercent);
}

function updateBarColor(bar, percentage) {
  if (percentage >= 85) {
    bar.style.backgroundColor = "#28a745"; // Excellent - Green
  } else if (percentage >= 70) {
    bar.style.backgroundColor = "#17a2b8"; // Good - Blue
  } else if (percentage >= 50) {
    bar.style.backgroundColor = "#ffc107"; // Average - Yellow
    bar.style.color = "#333"; // Dark text for yellow background
  } else {
    bar.style.backgroundColor = "#dc3545"; // Poor - Red
  }
}

// Apply preset template
function applyPreset(presetName) {
  const preset = presets[presetName];
  if (preset) {
    attendanceMaxInput.value = preset.attendance.max;
    assignmentsMaxInput.value = preset.assignments.max;
    engagementMaxInput.value = preset.engagement.max;

    // Clear value inputs
    attendanceInput.value = "";
    assignmentsInput.value = "";
    engagementInput.value = "";

    updateProgressBars();
  }
}

// Add preset button listeners
document.querySelectorAll(".preset-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    applyPreset(btn.dataset.preset);
  });
});

// Add event listeners for real-time updates
[
  attendanceInput,
  attendanceMaxInput,
  assignmentsInput,
  assignmentsMaxInput,
  engagementInput,
  engagementMaxInput,
].forEach((input) => {
  input.addEventListener("input", updateProgressBars);
});

function setLoading(isLoading) {
  if (isLoading) {
    predictBtn.disabled = true;
    predictBtn.innerHTML = '<span class="button-icon">⏳</span> Calculating...';
    predictionResult.innerHTML =
      '<div class="loading-spinner">Calculating your performance...</div>';
  } else {
    predictBtn.disabled = false;
    predictBtn.innerHTML =
      '<span class="button-icon">🎯</span> Calculate My Performance';
  }
}

function getDetailedFeedback(prediction, percentages) {
  const feedback = {
    Excellent: {
      icon: "🌟",
      message: "Outstanding performance! Keep up the great work!",
      tips: [
        "Continue your excellent study habits",
        "Consider helping peers who are struggling",
        "Take on additional challenges",
      ],
    },
    Good: {
      icon: "👍",
      message: "Good job! You're on the right track.",
      tips: [
        "Try to participate more in class discussions",
        "Review areas where you scored lower",
        "Set goals to reach the Excellent category",
      ],
    },
    Average: {
      icon: "📚",
      message: "You're doing okay, but there's room for improvement.",
      tips: [
        "Focus on increasing your attendance",
        "Complete all pending assignments",
        "Engage more during class activities",
      ],
    },
    Poor: {
      icon: "⚠️",
      message: "You need to improve your performance.",
      tips: [
        "Talk to your teachers for help",
        "Create a study plan and schedule",
        "Join study groups for support",
      ],
    },
  };

  const defaultFeedback = {
    icon: "📊",
    message: "Performance assessment complete.",
    tips: ["Review the guidelines to understand your score"],
  };

  const result = feedback[prediction] || defaultFeedback;

  // Add specific tips based on lowest percentage
  const lowestCategory = Object.keys(percentages).reduce((a, b) =>
    percentages[a] < percentages[b] ? a : b
  );

  const lowestTips = {
    attendance:
      "📅 Your attendance needs attention - try to attend more classes",
    assignments: "📝 Focus on completing more assignments on time",
    engagement: "💬 Participate more in class discussions and activities",
  };

  result.tips.push(lowestTips[lowestCategory]);

  return result;
}

function displayResult(data) {
  // Get current values and calculate percentages
  const attendanceVal = parseFloat(attendanceInput.value) || 0;
  const attendanceMax = parseFloat(attendanceMaxInput.value) || 1;
  const assignmentsVal = parseFloat(assignmentsInput.value) || 0;
  const assignmentsMax = parseFloat(assignmentsMaxInput.value) || 1;
  const engagementVal = parseFloat(engagementInput.value) || 0;
  const engagementMax = parseFloat(engagementMaxInput.value) || 1;

  const percentages = {
    attendance: calculatePercentage(attendanceVal, attendanceMax),
    assignments: calculatePercentage(assignmentsVal, assignmentsMax),
    engagement: calculatePercentage(engagementVal, engagementMax),
  };

  const overallAvg =
    (percentages.attendance +
      percentages.assignments +
      percentages.engagement) /
    3;

  const feedback = getDetailedFeedback(data.prediction, percentages);

  let resultClass = data.prediction.toLowerCase();

  predictionResult.innerHTML = `
        <div class="result ${resultClass}">
            <div class="result-header">
                <span class="result-icon">${feedback.icon}</span>
                <h3>${data.prediction}</h3>
            </div>
            <p class="feedback-message">${feedback.message}</p>
            
            <div class="score-breakdown">
                <h4>📊 Your Score Breakdown:</h4>
                <div class="breakdown-item">
                    <span>📅 Attendance:</span>
                    <strong>${attendanceVal}/${attendanceMax} (${Math.round(
    percentages.attendance
  )}%)</strong>
                </div>
                <div class="breakdown-item">
                    <span>📝 Assignments:</span>
                    <strong>${assignmentsVal}/${assignmentsMax} (${Math.round(
    percentages.assignments
  )}%)</strong>
                </div>
                <div class="breakdown-item">
                    <span>💬 Engagement:</span>
                    <strong>${engagementVal}/${engagementMax} (${Math.round(
    percentages.engagement
  )}%)</strong>
                </div>
                <div class="breakdown-item total">
                    <span>📈 Overall Average:</span>
                    <strong>${Math.round(overallAvg)}%</strong>
                </div>
            </div>
            
            <div class="improvement-tips">
                <h4>💡 Improvement Tips:</h4>
                <ul class="tips-list">
                    ${feedback.tips.map((tip) => `<li>${tip}</li>`).join("")}
                </ul>
            </div>
            
            <div class="encouragement">
                <p>✨ Keep working hard! Every small improvement counts.</p>
            </div>
        </div>
    `;
}

studentForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  // Get input values and max values
  const attendance = parseFloat(attendanceInput.value);
  const attendanceMax = parseFloat(attendanceMaxInput.value);
  const assignments = parseFloat(assignmentsInput.value);
  const assignmentsMax = parseFloat(assignmentsMaxInput.value);
  const engagement = parseFloat(engagementInput.value);
  const engagementMax = parseFloat(engagementMaxInput.value);

  // Validate inputs
  if (attendance < 0 || attendance > attendanceMax) {
    predictionResult.innerHTML = `<p class="error">❌ Attendance cannot exceed ${attendanceMax}</p>`;
    return;
  }
  if (assignments < 0 || assignments > assignmentsMax) {
    predictionResult.innerHTML = `<p class="error">❌ Assignments cannot exceed ${assignmentsMax}</p>`;
    return;
  }
  if (engagement < 0 || engagement > engagementMax) {
    predictionResult.innerHTML = `<p class="error">❌ Engagement cannot exceed ${engagementMax}</p>`;
    return;
  }

  // Calculate percentages for the model
  const attendancePct = (attendance / attendanceMax) * 100;
  const assignmentsPct = (assignments / assignmentsMax) * 100;
  const engagementPct = (engagement / engagementMax) * 100;

  setLoading(true);

  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        attendance: attendancePct,
        assignments: assignmentsPct,
        engagement: engagementPct,
        // Also send raw values for display
        rawData: {
          attendance: { value: attendance, max: attendanceMax },
          assignments: { value: assignments, max: assignmentsMax },
          engagement: { value: engagement, max: engagementMax },
        },
      }),
    });

    const data = await response.json();

    if (response.ok) {
      console.log("Prediction result:", data);
      displayResult(data);
    } else {
      predictionResult.innerHTML = `<p class="error">❌ Error: ${
        data.error || "Prediction failed"
      }</p>`;
    }
  } catch (error) {
    console.error("Fetch error:", error);
    predictionResult.innerHTML =
      '<p class="error">❌ Network error. Please try again.</p>';
  } finally {
    setLoading(false);
  }
});

// Initialize progress bars on page load
updateProgressBars();

// Add validation to ensure value doesn't exceed max
function validateValueInput(valueInput, maxInput) {
  valueInput.addEventListener("change", () => {
    const value = parseFloat(valueInput.value) || 0;
    const max = parseFloat(maxInput.value) || 1;
    if (value > max) {
      valueInput.value = max;
      updateProgressBars();
    }
  });
}

validateValueInput(attendanceInput, attendanceMaxInput);
validateValueInput(assignmentsInput, assignmentsMaxInput);
validateValueInput(engagementInput, engagementMaxInput);

async function debugEnrollment() {
  try {
    const response = await fetch("/api/my_courses");
    const courses = await response.json();
    document.getElementById("debugInfo").innerHTML = `
            ✅ My Courses: ${courses.length} courses<br>
            ${courses.map((c) => `- ${c.name} (ID: ${c.id})`).join("<br>")}
        `;
  } catch (error) {
    document.getElementById(
      "debugInfo"
    ).innerHTML = `❌ Error: ${error.message}`;
  }
}

// Call it after loading courses
setTimeout(debugEnrollment, 2000);
