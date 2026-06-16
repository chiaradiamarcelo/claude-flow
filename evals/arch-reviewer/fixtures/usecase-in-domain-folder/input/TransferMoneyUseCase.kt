package banking.domain.models.account

class TransferMoneyUseCase(
    private val accounts: AccountRepository,
) {
    fun execute(fromId: String, toId: String, amountCents: Long) {
        val from = accounts.findById(fromId)
        val to = accounts.findById(toId)
        from.withdraw(amountCents)
        to.deposit(amountCents)
        accounts.save(from)
        accounts.save(to)
    }
}
