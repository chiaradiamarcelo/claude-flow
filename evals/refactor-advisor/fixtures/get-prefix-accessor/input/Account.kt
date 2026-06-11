package banking.domain.models.account

class Account(
    private val id: String,
    private var balanceCents: Long,
) {
    fun getId(): String = id

    fun getBalanceCents(): Long = balanceCents

    fun deposit(amountCents: Long) {
        balanceCents += amountCents
    }
}
