class GetAccountBalanceTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var getBalance: GetBalance

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        getBalance = GetBalance(accounts)
    }

    @Test
    fun returns_the_balance_of_the_requested_account() {
        accounts.save(BankAccount(ACCOUNT_ID, balance = 100))
        accounts.save(BankAccount("OTHER-1", balance = 999))
        accounts.save(BankAccount("OTHER-2", balance = 888))
        accounts.save(BankAccount("OTHER-3", balance = 777))
        accounts.save(BankAccount("OTHER-4", balance = 666))

        val balance = getBalance.execute(ACCOUNT_ID)

        assertThat(balance).isEqualTo(100)
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
