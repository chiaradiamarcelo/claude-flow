package com.example.bank.infrastructure.persistence

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountRepository
import org.springframework.stereotype.Repository

@Repository
class AccountRepositoryAdapter(
    private val accountJpaRepository: AccountJpaRepository,
) : AccountRepository {

    override fun save(account: Account) {
        accountJpaRepository.save(entityFor(account))
    }

    override fun findById(accountId: String): Account? =
        accountJpaRepository.findById(accountId).map(::accountFor).orElse(null)

    private fun entityFor(account: Account) = AccountJpaEntity(account.accountId(), account.balance())

    private fun accountFor(entity: AccountJpaEntity) = Account(entity.accountId, entity.balance)
}
