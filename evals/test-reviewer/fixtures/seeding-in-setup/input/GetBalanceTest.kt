class GetBalanceTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var getBalance: GetBalance

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        getBalance = GetBalance(accounts)
        accounts.save(BankAccount(ACCOUNT_ID, balance = 100))
    }

    @Test
    fun returns_the_current_balance() {
        val balance = getBalance.execute(ACCOUNT_ID)

        assertThat(balance).isEqualTo(100)
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
