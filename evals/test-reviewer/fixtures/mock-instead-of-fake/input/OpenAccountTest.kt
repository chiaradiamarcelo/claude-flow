class OpenAccountTest {

    private lateinit var accounts: AccountRepository
    private lateinit var openAccount: OpenAccount

    @BeforeEach
    fun setUp() {
        accounts = mock(AccountRepository::class.java)
        openAccount = OpenAccount(accounts)
    }

    @Test
    fun saves_a_new_account_with_a_zero_balance() {
        openAccount.execute(ACCOUNT_ID)

        verify(accounts).save(BankAccount(ACCOUNT_ID, balance = 0))
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
