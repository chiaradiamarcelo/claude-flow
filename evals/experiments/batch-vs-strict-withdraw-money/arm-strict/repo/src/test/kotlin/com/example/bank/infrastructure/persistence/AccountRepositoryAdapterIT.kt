package com.example.bank.infrastructure.persistence

import com.example.bank.domain.models.account.AccountRepository
import com.example.bank.domain.models.account.AccountRepositoryContractTest
import org.junit.jupiter.api.BeforeEach
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest
import org.springframework.context.annotation.Import

@DataJpaTest
@Import(AccountRepositoryAdapter::class)
class AccountRepositoryAdapterIT : AccountRepositoryContractTest() {

    @Autowired
    private lateinit var adapter: AccountRepositoryAdapter

    override lateinit var repository: AccountRepository

    @BeforeEach
    fun setUp() {
        repository = adapter
    }
}
