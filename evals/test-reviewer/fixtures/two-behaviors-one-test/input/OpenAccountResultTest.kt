class OpenAccountResultTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var openAccount: OpenAccount

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        openAccount = OpenAccount(accounts)
    }

    @Test
    fun saves_the_account_and_returns_its_id() {
        val id = openAccount.execute(ACCOUNT_ID)

        assertThat(id).isEqualTo(ACCOUNT_ID)
        assertThat(accounts.byId(ACCOUNT_ID).balance).isEqualTo(0)
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
