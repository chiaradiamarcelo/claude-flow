package banking.domain.models.account

class Account private constructor(
    val id: String,
    private var balanceCents: Long,
) {
    fun balance(): Long = balanceCents

    fun deposit(amountCents: Long) {
        require(!isNegative(amountCents)) { "amount must be positive" }
        balanceCents += amountCents
    }

    private fun isNegative(amountCents: Long): Boolean = amountCents < 0

    override fun equals(other: Any?): Boolean = other is Account && other.id == id

    override fun hashCode(): Int = id.hashCode()

    companion object {
        fun open(id: String, openingBalanceCents: Long): Account {
            require(openingBalanceCents >= 0) { "opening balance must be non-negative" }
            return Account(id, openingBalanceCents)
        }
    }
}
