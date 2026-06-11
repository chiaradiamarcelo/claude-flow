package banking.domain.models.account

import jakarta.persistence.Entity
import jakarta.persistence.Id
import org.springframework.data.annotation.Version

@Entity
class Account(
    @Id val id: String,
    @Version var version: Long,
    var balanceCents: Long,
) {
    fun deposit(amountCents: Long) {
        balanceCents += amountCents
    }
}
