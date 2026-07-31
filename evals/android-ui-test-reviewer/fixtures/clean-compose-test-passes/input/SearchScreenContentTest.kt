class SearchScreenContentTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `shows festival list when state is loaded`() {
        composeTestRule.setContent {
            SearchScreenContent(state = SearchUiState.Loaded(festivals = listOf(aFestival("Primavera"))))
        }

        composeTestRule.onNodeWithTag(SearchTags.FESTIVAL_LIST).assertIsDisplayed()
        composeTestRule.onNodeWithText("Primavera").assertIsDisplayed()
    }

    @Test
    fun `shows empty message when state is empty`() {
        composeTestRule.setContent {
            SearchScreenContent(state = SearchUiState.Empty)
        }

        composeTestRule.onNodeWithTag(SearchTags.EMPTY_MESSAGE).assertIsDisplayed()
    }
}
