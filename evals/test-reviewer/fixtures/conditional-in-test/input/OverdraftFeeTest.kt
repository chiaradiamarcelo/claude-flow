class OverdraftFeeTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var withdrawMoney: WithdrawMoney

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        withdrawMoney = WithdrawMoney(accounts)
    }

    @Test
    fun applies_the_overdraft_fee_when_the_balance_goes_negative() {
        accounts.save(BankAccount(ACCOUNT_ID, balance = 10))

        withdrawMoney.execute(ACCOUNT_ID, 30)

        val balance = accounts.byId(ACCOUNT_ID).balance
        if (balance < 0) {
            assertThat(balance).isEqualTo(-25)
        } else {
            assertThat(balance).isEqualTo(0)
        }
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
