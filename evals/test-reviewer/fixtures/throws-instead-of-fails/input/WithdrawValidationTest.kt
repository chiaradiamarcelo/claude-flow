class WithdrawValidationTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var withdrawMoney: WithdrawMoney

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        withdrawMoney = WithdrawMoney(accounts)
    }

    @Test
    fun throws_when_the_amount_is_greater_than_the_balance() {
        accounts.save(BankAccount(ACCOUNT_ID, balance = 20))

        val result = withdrawMoney.execute(ACCOUNT_ID, 50)

        assertThat(result).isFailureOf(InsufficientFunds::class)
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
