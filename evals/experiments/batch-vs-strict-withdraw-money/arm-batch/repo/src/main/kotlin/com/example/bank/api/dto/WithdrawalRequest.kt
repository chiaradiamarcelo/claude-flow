package com.example.bank.api.dto

import java.math.BigDecimal

/**
 * Format-only contract: [amount] must be present and parseable as a number.
 * Positivity and overdraft rules belong to the domain.
 */
data class WithdrawalRequest(val amount: BigDecimal)
