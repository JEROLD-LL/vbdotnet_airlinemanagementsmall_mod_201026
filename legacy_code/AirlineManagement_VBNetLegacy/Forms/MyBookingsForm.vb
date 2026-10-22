Imports System.Windows.Forms

Public Class MyBookingsForm
    Inherits Form

    Private dgvBookings As DataGridView
    Private btnRefresh As Button
    Private btnView As Button
    Private btnEdit As Button
    Private btnDelete As Button

    Public Sub New()
        InitializeComponent()
        LoadBookings()
    End Sub

    Private Sub InitializeComponent()
        Me.Text = "My Bookings"
        Me.Size = New Size(1200, 500)
        Me.StartPosition = FormStartPosition.CenterScreen

        ' Data Grid View
        dgvBookings = New DataGridView()
        dgvBookings.Location = New Point(10, 10)
        dgvBookings.Size = New Size(1160, 400)
        dgvBookings.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
        dgvBookings.SelectionMode = DataGridViewSelectionMode.FullRowSelect
        dgvBookings.ReadOnly = True
        dgvBookings.AllowUserToAddRows = False
        Me.Controls.Add(dgvBookings)

        ' Buttons
        btnRefresh = New Button()
        btnRefresh.Text = "Refresh"
        btnRefresh.Location = New Point(10, 420)
        btnRefresh.Size = New Size(100, 30)
        AddHandler btnRefresh.Click, AddressOf BtnRefresh_Click
        Me.Controls.Add(btnRefresh)

        btnView = New Button()
        btnView.Text = "View"
        btnView.Location = New Point(120, 420)
        btnView.Size = New Size(100, 30)
        AddHandler btnView.Click, AddressOf BtnView_Click
        Me.Controls.Add(btnView)

        btnEdit = New Button()
        btnEdit.Text = "Edit"
        btnEdit.Location = New Point(230, 420)
        btnEdit.Size = New Size(100, 30)
        AddHandler btnEdit.Click, AddressOf BtnEdit_Click
        Me.Controls.Add(btnEdit)

        btnDelete = New Button()
        btnDelete.Text = "Delete"
        btnDelete.Location = New Point(340, 420)
        btnDelete.Size = New Size(100, 30)
        AddHandler btnDelete.Click, AddressOf BtnDelete_Click
        Me.Controls.Add(btnDelete)
    End Sub

    Private Sub LoadBookings()
        If Not SessionManager.IsAuthenticated() Then
            MessageBox.Show("Please login first.", "Not Authenticated", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            Me.Close()
            Return
        End If

        Dim bookings As List(Of Booking) = BookingRepository.GetByUserId(SessionManager.CurrentUser.Id)

        dgvBookings.Columns.Clear()
        dgvBookings.Columns.Add("Id", "ID")
        dgvBookings.Columns("Id").Visible = False
        dgvBookings.Columns.Add("FlightId", "Flight ID")
        dgvBookings.Columns("FlightId").Visible = False
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
            dgvBookings.Rows.Add(booking.Id, booking.FlightId, flight.FlightNumber,
                               flight.Origin & " → " & flight.Destination,
                               flight.DepartureDate.ToString("yyyy-MM-dd"),
                               flight.DepartureTime.ToString("hh\:mm"),
                               flight.ArrivalTime.ToString("hh\:mm"),
                               booking.PassengerName, booking.PassengerEmail,
                               If(String.IsNullOrEmpty(booking.SeatNumber), "N/A", booking.SeatNumber),
                               flight.Price, booking.BookingDate.ToString("yyyy-MM-dd HH:mm"))
        Next
    End Sub

    Private Function GetSelectedBookingId() As Integer?
        If dgvBookings.SelectedRows.Count > 0 Then
            Return Convert.ToInt32(dgvBookings.SelectedRows(0).Cells("Id").Value)
        End If
        Return Nothing
    End Function

    Private Sub BtnRefresh_Click(sender As Object, e As EventArgs)
        LoadBookings()
    End Sub

    Private Sub BtnView_Click(sender As Object, e As EventArgs)
        Dim bookingId As Integer? = GetSelectedBookingId()
        If bookingId.HasValue Then
            Dim viewForm As New ViewBookingForm(bookingId.Value)
            viewForm.ShowDialog()
        Else
            MessageBox.Show("Please select a booking.", "No Selection", MessageBoxButtons.OK, MessageBoxIcon.Warning)
        End If
    End Sub

    Private Sub BtnEdit_Click(sender As Object, e As EventArgs)
        Dim bookingId As Integer? = GetSelectedBookingId()
        If bookingId.HasValue Then
            Dim editForm As New EditBookingForm(bookingId.Value)
            editForm.ShowDialog()
            LoadBookings()
        Else
            MessageBox.Show("Please select a booking.", "No Selection", MessageBoxButtons.OK, MessageBoxIcon.Warning)
        End If
    End Sub

    Private Sub BtnDelete_Click(sender As Object, e As EventArgs)
        Dim bookingId As Integer? = GetSelectedBookingId()
        If bookingId.HasValue Then
            If MessageBox.Show("Are you sure you want to delete this booking?", "Confirm Delete", MessageBoxButtons.YesNo, MessageBoxIcon.Question) = DialogResult.Yes Then
                Dim errorMsg As String = BookingService.DeleteBooking(bookingId.Value, SessionManager.CurrentUser.Id)
                If String.IsNullOrEmpty(errorMsg) Then
                    MessageBox.Show("Booking deleted successfully!", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
                    LoadBookings()
                Else
                    MessageBox.Show(errorMsg, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
                End If
            End If
        Else
            MessageBox.Show("Please select a booking.", "No Selection", MessageBoxButtons.OK, MessageBoxIcon.Warning)
        End If
    End Sub
End Class

