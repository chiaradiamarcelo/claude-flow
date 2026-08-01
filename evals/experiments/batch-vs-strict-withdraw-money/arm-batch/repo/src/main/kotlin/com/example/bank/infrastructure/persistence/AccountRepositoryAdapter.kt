package com.example.bank.infrastructure.persistence

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountRepository
import org.springframework.stereotype.Repository

@Repository
class AccountRepositoryAdapter(
    private val accountJpaRepository: AccountJpaRepository,
) : AccountRepository {

    override fun save(account: Account) {
        accountJpaRepository.save(toJpaEntity(account))
    }

    override fun findById(accountId: String): Account? =
        accountJpaRepository.findById(accountId).map(::toAccount).orElse(null)

    private fun toJpaEntity(account: Account): AccountJpaEntity =
        AccountJpaEntity(accountId = account.accountId(), balance = account.balance())

    private fun toAccount(entity: AccountJpaEntity): Account =
        Account(entity.accountId, entity.balance)
}
