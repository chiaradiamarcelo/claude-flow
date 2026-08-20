package com.example.presentation

class SurveyScreenModel(
    private val completeSurvey: CompleteSurvey,
) {
    /**
     * The completion flag is recomputed by the profile service on every read rather than
     * stored, which is why this waits for the re-read instead of patching the flag into local
     * state. A local patch only hid the redirect for that session; the next login recomputed
     * the flag, found the answers missing, and returned the user to question one.
     */
    suspend fun onFinish(given: List<Answer>) {
        when (completeSurvey(currentSurveyId, given)) {
            Completion.Done -> navigator.toDashboard()
            Completion.Unconfirmed -> state.showUnconfirmed()
        }
    }
}
