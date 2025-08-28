// Main JavaScript for UAS Exam System

// Import Bootstrap
const bootstrap = window.bootstrap

document.addEventListener("DOMContentLoaded", () => {
  // Initialize tooltips
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))

  // Auto-hide alerts after 5 seconds
  setTimeout(() => {
    var alerts = document.querySelectorAll(".alert")
    alerts.forEach((alert) => {
      var bsAlert = new bootstrap.Alert(alert)
      bsAlert.close()
    })
  }, 5000)
})

// Exam timer functionality
let examTimer = null
let timeRemaining = 0

function startTimer(duration, display) {
  timeRemaining = duration
  examTimer = setInterval(() => {
    const minutes = Math.floor(timeRemaining / 60)
    const seconds = timeRemaining % 60

    display.textContent = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`

    if (timeRemaining <= 0) {
      clearInterval(examTimer)
      autoSubmitExam()
    }

    timeRemaining--
  }, 1000)
}

function autoSubmitExam() {
  alert("Time is up! Your exam will be automatically submitted.")
  // Auto-submit logic will be implemented later
  if (document.getElementById("exam-form")) {
    document.getElementById("exam-form").submit()
  }
}

// Question selection functionality
function selectOption(questionId, optionId) {
  // Remove previous selection
  const options = document.querySelectorAll(`input[name="question_${questionId}"]`)
  const optionButtons = document.querySelectorAll(`.option-button[data-question="${questionId}"]`)

  optionButtons.forEach((button) => {
    button.classList.remove("selected")
  })

  // Select new option
  const selectedButton = document.querySelector(
    `.option-button[data-question="${questionId}"][data-option="${optionId}"]`,
  )
  if (selectedButton) {
    selectedButton.classList.add("selected")
  }

  // Update hidden input
  const hiddenInput = document.querySelector(`input[name="question_${questionId}"][value="${optionId}"]`)
  if (hiddenInput) {
    hiddenInput.checked = true
  }

  // Auto-save answer
  autoSaveAnswer(questionId, optionId)
}

function autoSaveAnswer(questionId, optionId) {
  // Auto-save functionality will be implemented with AJAX
  console.log(`Auto-saving: Question ${questionId}, Option ${optionId}`)
}

// Prevent accidental page refresh during exam
window.addEventListener("beforeunload", (e) => {
  if (document.body.classList.contains("exam-in-progress")) {
    e.preventDefault()
    e.returnValue = "Are you sure you want to leave? Your exam progress may be lost."
    return e.returnValue
  }
})
