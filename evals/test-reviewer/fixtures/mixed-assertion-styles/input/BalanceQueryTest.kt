class BalanceQueryTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var getBalance: GetBalance

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        getBalance = GetBalance(accounts)
    }

    @Test
    fun returns_the_balance_for_an_existing_account() {
        accounts.save(BankAccount(ACCOUNT_ID, balance = 100))

        val balance = getBalance.execute(ACCOUNT_ID)

        assertEquals(100, balance)
    }

    @Test
    fun returns_zero_for_a_newly_opened_account() {
        accounts.save(BankAccount(ACCOUNT_ID, balance = 0))

        val balance = getBalance.execute(ACCOUNT_ID)

        assertThat(balance).isEqualTo(0)
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
