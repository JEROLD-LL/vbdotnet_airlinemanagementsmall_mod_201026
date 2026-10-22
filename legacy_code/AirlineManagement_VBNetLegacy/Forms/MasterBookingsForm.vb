Imports System.Windows.Forms

Public Class MasterBookingsForm
    Inherits Form

    Private dgvBookings As DataGridView
    Private btnRefresh As Button

    Public Sub New()
        InitializeComponent()
        LoadBookings()
    End Sub

    Private Sub InitializeComponent()
        Me.Text = "Master Bookings"
        Me.Size = New Size(1400, 500)
        Me.StartPosition = FormStartPosition.CenterScreen

        ' Data Grid View
        dgvBookings = New DataGridView()
        dgvBookings.Location = New Point(10, 10)
        dgvBookings.Size = New Size(1360, 400)
        dgvBookings.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
        dgvBookings.SelectionMode = DataGridViewSelectionMode.FullRowSelect
        dgvBookings.ReadOnly = True
        dgvBookings.AllowUserToAddRows = False
        Me.Controls.Add(dgvBookings)

        ' Refresh button
        btnRefresh = New Button()
        btnRefresh.Text = "Refresh"
        btnRefresh.Location = New Point(10, 420)
        btnRefresh.Size = New Size(100, 30)
        AddHandler btnRefresh.Click, AddressOf BtnRefresh_Click
        Me.Controls.Add(btnRefresh)
    End Sub

    Private Sub LoadBookings()
        Dim bookings As List(Of Booking) = BookingRepository.GetAll()

        dgvBookings.Columns.Clear()
        dgvBookings.Columns.Add("Id", "Booking ID")
        dgvBookings.Columns.Add("User", "User")
        dgvBookings.Columns.Add("FlightNumber", "Flight Number")
        dgvBookings.Columns.Add("Route", "Route")
        dgvBookings.Columns.Add("DepartureDate", "Departure Date")
        dgvBookings.Columns.Add("DepartureTime", "Departure Time")
        dgvBookings.Columns.Add("ArrivalTime", "Arrival Time")
        dgvBookings.Columns.Add("PassengerName", "Passenger Name")
        dgvBookings.Columns.Add("PassengerEmail", "Passenger Email")
        dgvBookings.Columns.Add("SeatNumber", "Seat Number")
        dgvBookings.Columns.Add("Price", "Price")
        dgvBookings.Columns("Price").DefaultCellStyle.Format = "C"
        dgvBookings.Columns.Add("BookingDate", "Booking Date")

        dgvBookings.Rows.Clear()
        For Each booking In bookings
            Dim flight As Flight = FlightRepository.GetById(booking.FlightId)
            Dim userDisplay As String = "Guest"
            If booking.UserId.HasValue Then
                Dim user As User = UserRepository.GetById(booking.UserId.Value)
                If user IsNot Nothing Then
                    userDisplay = user.Username & " (" & user.FullName & ")"
                End If
            End If

            dgvBookings.Rows.Add("#" & booking.Id, userDisplay, flight.FlightNumber,
                               flight.Origin & " → " & flight.Destination,
                               flight.DepartureDate.ToString("yyyy-MM-dd"),
                               flight.DepartureTime.ToString("hh\:mm"),
                               flight.ArrivalTime.ToString("hh\:mm"),
                               booking.PassengerName, booking.PassengerEmail,
                               If(String.IsNullOrEmpty(booking.SeatNumber), "N/A", booking.SeatNumber),
                               flight.Price, booking.BookingDate.ToString("yyyy-MM-dd HH:mm:ss"))
        Next
    End Sub

    Private Sub BtnRefresh_Click(sender As Object, e As EventArgs)
        LoadBookings()
    End Sub
End Class

