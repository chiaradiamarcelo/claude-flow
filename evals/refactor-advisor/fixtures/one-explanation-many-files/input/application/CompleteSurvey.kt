package com.example.application

class CompleteSurvey(
    private val answers: AnswerRepository,
    private val profile: ProfileQuery,
) {
    /**
     * The completion flag is not stored: the profile service recomputes it from the saved
     * answers on every read. So the survey has to read the profile back after writing —
     * patching the flag locally only hides the redirect until the next session, when the
     * recompute finds the answers missing and sends the user back to question one.
     */
    suspend operator fun invoke(surveyId: SurveyId, given: List<Answer>): Completion {
        answers.save(surveyId, given)
        return if (profile.reread().surveyCompleted) Completion.Done else Completion.Unconfirmed
    }
}
