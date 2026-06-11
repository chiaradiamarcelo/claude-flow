class CreateAccountTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var openAccount: OpenAccount

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        openAccount = OpenAccount(accounts)
    }

    @Test
    fun creates_an_account() {
        val account = openAccount.execute(ACCOUNT_ID)

        assertThat(account).isNotNull()
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
