class CreditAccountTest {

    private lateinit var accounts: FakeBankAccountRepository
    private lateinit var creditAccount: CreditAccount

    @BeforeEach
    fun setUp() {
        accounts = FakeBankAccountRepository()
        creditAccount = CreditAccount(accounts)
    }

    @Test
    fun increases_the_balance_by_the_credited_amount() {
        accounts.save(BankAccount("ACC-001", balance = 100))

        creditAccount.execute("ACC-001", 50)

        assertThat(accounts.findById("ACC-001").balance).isEqualTo(150)
    }

    @Test
    fun fails_when_the_amount_is_not_positive() {
        accounts.save(BankAccount("ACC-001", balance = 100))

        val result = creditAccount.execute("ACC-001", 0)

        assertThat(result).isFailureOf(NonPositiveAmount::class)
    }

    @Test
    fun fails_when_the_account_does_not_exist() {
        val result = creditAccount.execute("ACC-001", 50)

        assertThat(result).isFailureOf(AccountNotFound::class)
    }
}
