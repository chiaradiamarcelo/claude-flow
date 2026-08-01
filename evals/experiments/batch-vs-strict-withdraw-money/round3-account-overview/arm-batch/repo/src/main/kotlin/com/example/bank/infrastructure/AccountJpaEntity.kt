package com.example.bank.infrastructure

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.math.BigDecimal

@Entity
@Table(name = "accounts")
class AccountJpaEntity(
    @Id
    @Column(name = "account_id")
    val accountId: String = "",

    @Column(name = "balance", nullable = false)
    val balance: BigDecimal = BigDecimal.ZERO,
)
