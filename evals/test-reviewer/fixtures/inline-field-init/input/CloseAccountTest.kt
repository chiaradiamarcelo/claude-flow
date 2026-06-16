class CloseAccountTest {

    private val accounts = FakeAccountRepository()
    private val closeAccount = CloseAccount(accounts)

    @Test
    fun marks_the_account_as_closed() {
        accounts.save(BankAccount(ACCOUNT_ID, balance = 0))

        closeAccount.execute(ACCOUNT_ID)

        assertThat(accounts.byId(ACCOUNT_ID).isClosed).isTrue()
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
