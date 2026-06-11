class WithdrawMoneyTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var withdrawMoney: WithdrawMoney

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        withdrawMoney = WithdrawMoney(accounts)
    }

    @Test
    fun reduces_the_balance_by_the_withdrawn_amount() {
        // Given
        accounts.save(BankAccount(ACCOUNT_ID, balance = 100))

        // When
        withdrawMoney.execute(ACCOUNT_ID, 30)

        // Then
        assertThat(accounts.byId(ACCOUNT_ID).balance).isEqualTo(70)
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}
