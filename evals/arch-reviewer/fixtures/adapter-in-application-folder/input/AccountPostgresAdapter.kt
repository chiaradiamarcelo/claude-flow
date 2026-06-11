package banking.application

import banking.domain.models.account.Account
import banking.domain.models.account.AccountRepository
import org.springframework.jdbc.core.JdbcTemplate

class AccountPostgresAdapter(
    private val jdbc: JdbcTemplate,
) : AccountRepository {

    override fun findById(id: String): Account {
        val balance = jdbc.queryForObject(
            "SELECT balance_cents FROM accounts WHERE id = ?", Long::class.java, id,
        )!!
        return Account(id, balance)
    }

    override fun save(account: Account) {
        jdbc.update(
            "UPDATE accounts SET balance_cents = ? WHERE id = ?",
            account.balance(), account.id,
        )
    }
}
