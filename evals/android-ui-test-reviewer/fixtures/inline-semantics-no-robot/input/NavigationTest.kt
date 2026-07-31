class NavigationTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `search scroll position survives tab switch`() {
        composeTestRule.setContent { VoyagerNavGraph() }
        composeTestRule.onNodeWithTag("nav_item_search").performClick()
        composeTestRule.waitForIdle()
        composeTestRule.onNodeWithTag("festival_list").performScrollToIndex(15)
        composeTestRule.waitForIdle()
        composeTestRule.onNodeWithTag("nav_item_home").performClick()
        composeTestRule.waitForIdle()
        composeTestRule.onNodeWithTag("nav_item_search").performClick()
        composeTestRule.waitForIdle()
        val nodes = composeTestRule.onAllNodesWithText("Festival 1").fetchSemanticsNodes()
        assert(nodes.isEmpty())
    }
}
