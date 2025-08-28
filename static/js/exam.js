// Enhanced exam functionality JavaScript

class ExamManager {
  constructor(examId) {
    this.examId = examId
    this.currentQuestionIndex = 0
    this.questions = []
    this.answers = {}
    this.timeRemaining = 0
    this.timerInterval = null
    this.autoSaveInterval = null
    this.sectionName = ""
    this.bootstrap = window.bootstrap // Declare bootstrap variable
    this.pendingAnswers = [] // Track pending answers for batch save
    this.lastSaveTime = Date.now()
    this.saveInProgress = false

    this.init()
  }

  async init() {
    try {
      await this.loadQuestions()
      this.setupEventListeners()
      this.startTimer()
      this.startAutoSave()
      this.displayQuestion(0)
      this.updateQuestionNavigator()

      // Mark body as exam in progress
      document.body.classList.add("exam-in-progress")
    } catch (error) {
      console.error("Failed to initialize exam:", error)
      alert("Failed to load exam. Please refresh the page.")
    }
  }

  async loadQuestions() {
    try {
      const response = await fetch(`/exams/api/questions/${this.examId}/`)
      if (!response.ok) {
        throw new Error("Failed to load questions")
      }

      const data = await response.json()
      this.questions = data.questions
      this.answers = data.existing_answers || {}
      this.timeRemaining = data.section.time_remaining
      this.sectionName = data.section.name

      // Update section name in UI
      const sectionNameElement = document.querySelector(".exam-title small")
      if (sectionNameElement) {
        sectionNameElement.textContent = this.sectionName
      }
    } catch (error) {
      console.error("Error loading questions:", error)
      throw error
    }
  }

  displayQuestion(index) {
    if (index < 0 || index >= this.questions.length) return

    const question = this.questions[index]
    this.currentQuestionIndex = index

    // Update question display
    const questionNumberEl = document.getElementById("questionNumber")
    const questionTextEl = document.getElementById("questionText")
    const questionOptionsEl = document.getElementById("questionOptions")

    if (questionNumberEl) questionNumberEl.textContent = index + 1
    if (questionTextEl) questionTextEl.innerHTML = `<p>${question.text}</p>`

    // Update options
    if (questionOptionsEl) {
      questionOptionsEl.innerHTML = ""

      question.options.forEach((option) => {
        const optionElement = document.createElement("div")
        optionElement.className = "option-button"
        optionElement.setAttribute("data-question", question.id)
        optionElement.setAttribute("data-option", option.id)

        if (this.answers[question.id] === option.letter) {
          optionElement.classList.add("selected")
        }

        optionElement.innerHTML = `
                    <div class="option-letter">${option.letter}</div>
                    <div class="option-text">${option.text}</div>
                `

        optionElement.addEventListener("click", () => {
          this.selectOption(question.id, option.id, option.letter)
        })

        questionOptionsEl.appendChild(optionElement)
      })
    }

    // Update navigation buttons
    const prevBtn = document.getElementById("prevBtn")
    const nextBtn = document.getElementById("nextBtn")

    if (prevBtn) prevBtn.disabled = index === 0
    if (nextBtn) nextBtn.disabled = index === this.questions.length - 1

    // Update progress
    this.updateProgress()
  }

  async selectOption(questionId, optionId, optionLetter) {
    // Update local state
    this.answers[questionId] = optionLetter

    // Update visual selection
    const questionOptions = document.querySelectorAll(`[data-question="${questionId}"]`)
    questionOptions.forEach((btn) => btn.classList.remove("selected"))

    const selectedOption = document.querySelector(`[data-question="${questionId}"][data-option="${optionId}"]`)
    if (selectedOption) {
      selectedOption.classList.add("selected")
    }

    this.pendingAnswers.push({
      question_id: questionId,
      option_id: optionId,
    })

    // Show saving indicator
    this.showAutoSaveIndicator("saving")

    // Save answer to server
    try {
      await this.saveAnswer(questionId, optionId)
    } catch (error) {
      console.error("Failed to save answer:", error)
    }

    // Update navigator
    this.updateQuestionNavigator()
  }

  async saveAnswer(questionId, optionId) {
    try {
      const response = await fetch("/exams/api/save-answer/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question_id: questionId,
          option_id: optionId,
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to save answer")
      }

      const data = await response.json()
      console.log("Answer saved:", data)
    } catch (error) {
      console.error("Error saving answer:", error)
      // Show user-friendly error message
      this.showNotification("Failed to save answer. Please try again.", "error")
    }
  }

  updateProgress() {
    const current = this.currentQuestionIndex + 1
    const total = this.questions.length

    const currentQuestionEl = document.getElementById("currentQuestion")
    const totalQuestionsEl = document.getElementById("totalQuestions")
    const progressBarEl = document.getElementById("progressBar")

    if (currentQuestionEl) currentQuestionEl.textContent = current
    if (totalQuestionsEl) totalQuestionsEl.textContent = total

    if (progressBarEl) {
      const percentage = (current / total) * 100
      progressBarEl.style.width = percentage + "%"
    }
  }

  updateQuestionNavigator() {
    const grid = document.getElementById("questionGrid")
    if (!grid) return

    grid.innerHTML = ""

    this.questions.forEach((question, index) => {
      const gridItem = document.createElement("div")
      gridItem.className = "question-grid-item"
      gridItem.textContent = index + 1

      if (index === this.currentQuestionIndex) {
        gridItem.classList.add("current")
      } else if (this.answers[question.id]) {
        gridItem.classList.add("answered")
      } else {
        gridItem.classList.add("unanswered")
      }

      gridItem.addEventListener("click", () => {
        this.displayQuestion(index)
        this.closeNavigator()
      })

      grid.appendChild(gridItem)
    })
  }

  startTimer() {
    this.updateTimerDisplay()

    this.timerInterval = setInterval(async () => {
      if (this.timeRemaining <= 0) {
        clearInterval(this.timerInterval)
        await this.autoSubmitSection()
        return
      }

      this.timeRemaining--
      this.updateTimerDisplay()

      // Check server time every minute
      if (this.timeRemaining % 60 === 0) {
        await this.syncTimeWithServer()
      }
    }, 1000)
  }

  updateTimerDisplay() {
    const minutes = Math.floor(this.timeRemaining / 60)
    const seconds = this.timeRemaining % 60

    const display = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`
    const timerDisplayEl = document.getElementById("timerDisplay")

    if (timerDisplayEl) {
      timerDisplayEl.textContent = display
    }

    // Change color when time is running low
    const timerElement = document.getElementById("examTimer")
    if (timerElement) {
      if (this.timeRemaining <= 300) {
        // 5 minutes
        timerElement.style.borderColor = "#ff4444"
        const timerDisplayEl = timerElement.querySelector(".timer-display")
        if (timerDisplayEl) {
          timerDisplayEl.style.color = "#ff4444"
        }
      } else if (this.timeRemaining <= 600) {
        // 10 minutes
        timerElement.style.borderColor = "#ffa500"
        const timerDisplayEl = timerElement.querySelector(".timer-display")
        if (timerDisplayEl) {
          timerDisplayEl.style.color = "#ffa500"
        }
      }
    }
  }

  async syncTimeWithServer() {
    try {
      const response = await fetch(`/exams/api/time-remaining/${this.examId}/`)
      if (response.ok) {
        const data = await response.json()
        this.timeRemaining = data.time_remaining

        if (data.auto_submit) {
          await this.autoSubmitSection()
        }
      }
    } catch (error) {
      console.error("Failed to sync time with server:", error)
    }
  }

  startAutoSave() {
    // Auto-save every 15 seconds (more frequent)
    this.autoSaveInterval = setInterval(async () => {
      await this.performAutoSave()
    }, 15000)

    // Also save on page visibility change (user switching tabs/minimizing)
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        this.performAutoSave()
      }
    })

    // Save before page unload
    window.addEventListener("beforeunload", (e) => {
      if (this.pendingAnswers.length > 0) {
        // Synchronous save for page unload
        navigator.sendBeacon(
          "/exams/api/auto-save/",
          JSON.stringify({
            answers: this.pendingAnswers,
            current_question_index: this.currentQuestionIndex,
          }),
        )
      }
    })
  }

  async performAutoSave() {
    if (this.saveInProgress || this.pendingAnswers.length === 0) {
      return
    }

    this.saveInProgress = true

    try {
      const response = await fetch("/exams/api/auto-save/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.getCSRFToken(),
        },
        body: JSON.stringify({
          answers: this.pendingAnswers,
          current_question_index: this.currentQuestionIndex,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          this.pendingAnswers = [] // Clear saved answers
          this.lastSaveTime = Date.now()
          this.showAutoSaveIndicator("saved")
        } else {
          this.showAutoSaveIndicator("error")
        }
      } else {
        this.showAutoSaveIndicator("error")
      }
    } catch (error) {
      console.error("Auto-save failed:", error)
      this.showAutoSaveIndicator("error")
    } finally {
      this.saveInProgress = false
    }
  }

  showAutoSaveIndicator(status) {
    const indicator = document.getElementById("autoSaveIndicator")
    if (!indicator) return

    indicator.className = "auto-save-indicator"

    switch (status) {
      case "saving":
        indicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
        indicator.classList.add("saving")
        break
      case "saved":
        indicator.innerHTML = '<i class="fas fa-check"></i> Saved'
        indicator.classList.add("saved")
        setTimeout(() => {
          indicator.classList.remove("saved")
          indicator.innerHTML = ""
        }, 2000)
        break
      case "error":
        indicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Save failed'
        indicator.classList.add("error")
        setTimeout(() => {
          indicator.classList.remove("error")
          indicator.innerHTML = ""
        }, 3000)
        break
    }
  }

  getCSRFToken() {
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")
    return csrfToken ? csrfToken.value : ""
  }

  async autoSubmitSection() {
    clearInterval(this.timerInterval)
    clearInterval(this.autoSaveInterval)

    this.showNotification("Time is up! Section will be automatically submitted.", "warning")

    // Submit section
    setTimeout(() => {
      window.location.href = `/exams/submit-section/${this.examId}/`
    }, 2000)
  }

  setupEventListeners() {
    // Navigation buttons
    const prevBtn = document.getElementById("prevBtn")
    const nextBtn = document.getElementById("nextBtn")
    const clearBtn = document.getElementById("clearBtn")
    const submitSectionBtn = document.getElementById("submitSectionBtn")

    if (prevBtn) {
      prevBtn.addEventListener("click", () => {
        if (this.currentQuestionIndex > 0) {
          this.displayQuestion(this.currentQuestionIndex - 1)
        }
      })
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        if (this.currentQuestionIndex < this.questions.length - 1) {
          this.displayQuestion(this.currentQuestionIndex + 1)
        }
      })
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        this.clearCurrentAnswer()
      })
    }

    if (submitSectionBtn) {
      submitSectionBtn.addEventListener("click", () => {
        this.showSubmitModal()
      })
    }

    // Navigator toggle
    const toggleNavigator = document.getElementById("toggleNavigator")
    const closeNavigator = document.getElementById("closeNavigator")

    if (toggleNavigator) {
      toggleNavigator.addEventListener("click", () => {
        this.toggleNavigator()
      })
    }

    if (closeNavigator) {
      closeNavigator.addEventListener("click", () => {
        this.closeNavigator()
      })
    }

    // Confirm submit
    const confirmSubmit = document.getElementById("confirmSubmit")
    if (confirmSubmit) {
      confirmSubmit.addEventListener("click", () => {
        this.submitSection()
      })
    }

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey || e.metaKey) return // Don't interfere with browser shortcuts

      switch (e.key) {
        case "ArrowLeft":
          e.preventDefault()
          if (this.currentQuestionIndex > 0) {
            this.displayQuestion(this.currentQuestionIndex - 1)
          }
          break
        case "ArrowRight":
          e.preventDefault()
          if (this.currentQuestionIndex < this.questions.length - 1) {
            this.displayQuestion(this.currentQuestionIndex + 1)
          }
          break
        case "1":
        case "2":
        case "3":
        case "4":
          e.preventDefault()
          this.selectOptionByNumber(Number.parseInt(e.key) - 1)
          break
      }
    })
  }

  selectOptionByNumber(optionIndex) {
    const currentQuestion = this.questions[this.currentQuestionIndex]
    if (currentQuestion && currentQuestion.options[optionIndex]) {
      const option = currentQuestion.options[optionIndex]
      this.selectOption(currentQuestion.id, option.id, option.letter)
    }
  }

  clearCurrentAnswer() {
    const currentQuestion = this.questions[this.currentQuestionIndex]
    if (currentQuestion) {
      delete this.answers[currentQuestion.id]
      this.displayQuestion(this.currentQuestionIndex)
    }
  }

  toggleNavigator() {
    const navigator = document.getElementById("questionNavigator")
    if (navigator) {
      navigator.classList.toggle("open")
    }
  }

  closeNavigator() {
    const navigator = document.getElementById("questionNavigator")
    if (navigator) {
      navigator.classList.remove("open")
    }
  }

  showSubmitModal() {
    const answeredCount = Object.keys(this.answers).length
    const totalCount = this.questions.length
    const unansweredCount = totalCount - answeredCount

    const summary = `
            <p>Questions answered: <strong>${answeredCount}</strong> out of <strong>${totalCount}</strong></p>
            ${unansweredCount > 0 ? `<p class="text-warning">Unanswered questions: <strong>${unansweredCount}</strong></p>` : ""}
        `

    const summaryEl = document.getElementById("submissionSummary")
    if (summaryEl) {
      summaryEl.innerHTML = summary
    }

    const modal = new this.bootstrap.Modal(document.getElementById("submitModal"))
    modal.show()
  }

  submitSection() {
    // Clear intervals
    clearInterval(this.timerInterval)
    clearInterval(this.autoSaveInterval)

    // Remove exam in progress class
    document.body.classList.remove("exam-in-progress")

    // Submit form
    const form = document.createElement("form")
    form.method = "POST"
    form.action = `/exams/submit-section/${this.examId}/`

    // Add CSRF token
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")
    if (csrfToken) {
      const csrfInput = document.createElement("input")
      csrfInput.type = "hidden"
      csrfInput.name = "csrfmiddlewaretoken"
      csrfInput.value = csrfToken.value
      form.appendChild(csrfInput)
    }

    document.body.appendChild(form)
    form.submit()
  }

  showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div")
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`
    notification.style.cssText = "top: 20px; right: 20px; z-index: 9999; min-width: 300px;"
    notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `

    document.body.appendChild(notification)

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification)
      }
    }, 5000)
  }

  cleanup() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval)
    }
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval)
    }
    document.body.classList.remove("exam-in-progress")
  }

  async checkSessionRecovery() {
    try {
      const response = await fetch(`/exams/api/session-status/${this.examId}/`)
      if (response.ok) {
        const data = await response.json()
        if (data.session_exists && data.can_resume) {
          const shouldRecover = confirm(
            `You have an interrupted exam session for "${data.exam_name}". ` +
              `You were in section "${data.current_section}" with ${data.completed_sections}/${data.total_sections} sections completed. ` +
              `Would you like to continue from where you left off?`,
          )

          if (shouldRecover) {
            window.location.href = `/exams/recover-session/${this.examId}/`
            return true
          }
        }
      }
    } catch (error) {
      console.error("Failed to check session recovery:", error)
    }
    return false
  }
}

// Initialize exam manager when page loads
document.addEventListener("DOMContentLoaded", async () => {
  const examIdElement = document.querySelector("[data-exam-id]")
  if (examIdElement) {
    const examId = examIdElement.dataset.examId
    const examManager = new ExamManager(examId)

    // Check for session recovery before starting new exam
    const recovered = await examManager.checkSessionRecovery()
    if (!recovered) {
      // Continue with normal initialization
      window.examManager = examManager
    }
  }
})

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
  if (window.examManager) {
    window.examManager.cleanup()
  }
})
