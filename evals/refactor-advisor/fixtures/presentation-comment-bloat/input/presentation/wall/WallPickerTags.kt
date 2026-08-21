package com.example.presentation.wall

/**
 * Test tags for the wall picker.
 *
 * Tags live in their own file rather than inline in the composables because a tag referenced from
 * an instrumented test and from a screen is shared vocabulary, and putting it in the screen file
 * would mean the test module depends on the screen file for a string constant. It was also tried
 * as a sealed class of tag types, which was rejected: the instrumented tests need plain strings
 * at the call site, so every assertion would have ended in `.value` for no benefit.
 */
object WallPickerTags {

    /**
     * The root of the picker sheet.
     */
    /**
     * Kept separate from the screen root so that `hasAnyAncestor` scoping can distinguish a node
     * inside the sheet from the same node behind it on the screen.
     */
    const val sheet = "wall_picker_sheet"

    /**
     * Tag for one selectable wall row.
     *
     * The wall id is lower-cased before it is interpolated, because the ids that come out of the
     * setter tooling are upper-case and the ones typed by hand are not, so two tags that name the
     * same wall would otherwise not match. Lower-casing here rather than in `WallId` keeps the
     * domain type free of a presentation concern — a tag is a UI detail and `WallId` should not
     * know that tags exist. This is also why the function takes the raw id rather than the typed
     * one: taking `WallId` would invite callers to think the case-folding is part of identity.
     */
    fun wallOptionTag(wallId: String): String = "wall_option_${wallId.lowercase()}"

    /**
     * The confirm button.
     *
     * Tapping confirm with no wall selected does nothing rather than dismissing the sheet: a
     * dismissal would look like a successful pick to the caller, and the caller has no way to
     * tell an empty pick from a cancelled one. See `a_confirm_with_no_selection_keeps_the_sheet_open`.
     */
    const val confirm = "wall_picker_confirm"

    // The search field. Uses the same prefix as the rest of the picker's tags.
    const val search = "wall_picker_search"
}
