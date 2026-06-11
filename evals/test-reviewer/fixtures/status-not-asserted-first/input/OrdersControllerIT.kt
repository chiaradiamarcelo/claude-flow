class OrdersControllerIT {

    private lateinit var useCase: ListOrders
    private lateinit var client: TestHttpClient

    @BeforeEach
    fun setUp() {
        useCase = mock(ListOrders::class.java)
        client = TestHttpClient(OrdersController(useCase))
    }

    @Test
    fun returns_200_with_the_orders() {
        whenever(useCase.allOrders()).thenReturn(listOf(Order("id_1", 99.99)))

        val response = client.get("/orders")

        assertThat(response.body).isEqualTo(listOf(mapOf("id" to "id_1", "amount" to 99.99)))
        assertThat(response.status).isEqualTo(200)
    }
}
