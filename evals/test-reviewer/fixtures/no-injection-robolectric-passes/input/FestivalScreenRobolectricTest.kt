@RunWith(AndroidJUnit4::class)
class FestivalScreenRobolectricTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `renders the festival title`() {
        composeTestRule.setContent {
            Text(text = stringResource(Res.string.festival_title))
        }

        composeTestRule.onNodeWithText("Primavera").assertIsDisplayed()
    }
}
