class WithdrawMoneyTest {

    private lateinit var accounts: FakeBankAccountRepository
    private lateinit var withdrawMoney: WithdrawMoney

    @BeforeEach
    fun setUp() {
        accounts = FakeBankAccountRepository()
        withdrawMoney = WithdrawMoney(accounts)
    }

    @Test
    fun reduces_the_balance_when_funds_are_sufficient() {
        accounts.save(BankAccount(ACCOUNT_ID, balance = 200))

        withdrawMoney.execute(ACCOUNT_ID, 50)

        assertThat(accounts.findById(ACCOUNT_ID).balance).isEqualTo(150)
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-001"
    }
}
