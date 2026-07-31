class SearchScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `shows festivals`() {
        val viewModel = SearchViewModel(FakeFestivalRepository(), SavedStateHandle())
        composeTestRule.setContent {
            SearchScreen(viewModel = viewModel)
        }

        composeTestRule.onNodeWithText("Primavera").assertIsDisplayed()
    }
}
