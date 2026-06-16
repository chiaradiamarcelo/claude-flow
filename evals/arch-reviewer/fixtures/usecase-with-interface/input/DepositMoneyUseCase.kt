package banking.application

interface DepositMoneyUseCase {
    fun execute(accountId: String, amountCents: Long): Long
}
