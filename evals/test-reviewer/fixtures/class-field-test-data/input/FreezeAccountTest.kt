class FreezeAccountTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var freezeAccount: FreezeAccount
    private val account = BankAccount(ACCOUNT_ID, balance = 250)

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        freezeAccount = FreezeAccount(accounts)
    }

    @Test
    fun marks_the_account_as_frozen() {
        accounts.save(account)

        freezeAccount.execute(ACCOUNT_ID)

        assertThat(accounts.byId(ACCOUNT_ID).isFrozen).isTrue()
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
