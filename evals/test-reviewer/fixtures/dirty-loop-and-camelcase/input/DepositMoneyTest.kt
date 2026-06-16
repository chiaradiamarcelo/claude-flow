class DepositMoneyTest {

    @Test
    fun depositsMoney() {
        val accounts = FakeBankAccountRepository()
        val depositMoney = DepositMoney(accounts)
        accounts.save(BankAccount("ACC-001", balance = 100))
        val amounts = listOf(10, 20, 30)
        for (amount in amounts) {
            depositMoney.execute("ACC-001", amount)
        }
        assertThat(accounts.findById("ACC-001").balance).isEqualTo(160)
    }
}
