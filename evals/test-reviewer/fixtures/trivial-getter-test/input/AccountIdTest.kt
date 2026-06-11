class AccountIdTest {

    @Test
    fun returns_the_id_it_was_constructed_with() {
        val account = BankAccount(ACCOUNT_ID, balance = 0)

        val id = account.id

        assertThat(id).isEqualTo(ACCOUNT_ID)
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
