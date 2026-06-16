class TransferMoneyTest {

    private lateinit var accounts: FakeBankAccountRepository
    private lateinit var transferMoney: TransferMoney

    @BeforeEach
    fun setUp() {
        accounts = FakeBankAccountRepository()
        transferMoney = TransferMoney(accounts)
    }

    @Test
    fun reduces_the_source_balance_by_the_transferred_amount() {
        accounts.save(BankAccount(SOURCE, balance = INITIAL_BALANCE))

        transferMoney.execute(SOURCE, DESTINATION, TRANSFER)

        assertThat(accounts.findById(SOURCE).balance).isEqualTo(EXPECTED_BALANCE)
    }

    companion object {
        private const val SOURCE = "ACC-001"
        private const val DESTINATION = "ACC-002"
        private const val INITIAL_BALANCE = 200
        private const val TRANSFER = 50
        private const val EXPECTED_BALANCE = 150
    }
}
