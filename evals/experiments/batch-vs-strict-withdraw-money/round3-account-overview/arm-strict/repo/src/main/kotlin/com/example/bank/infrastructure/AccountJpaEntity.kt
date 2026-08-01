package com.example.bank.infrastructure

import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.math.BigDecimal

@Entity
@Table(name = "accounts")
class AccountJpaEntity(
    @Id
    val accountId: String,
    val balance: BigDecimal,
)
