package com.matketing.be.domain.store.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalTime;
import java.util.UUID;

@Entity
@Table(name = "store_hours")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class StoreHours {

    @Id
    @Column(name = "store_id")
    private UUID storeId;

    @OneToOne(fetch = FetchType.LAZY)
    @MapsId
    @JoinColumn(name = "store_id")
    private Store store;

    @Column(name = "monday_open")
    private LocalTime mondayOpen;
    @Column(name = "monday_close")
    private LocalTime mondayClose;

    @Column(name = "tuesday_open")
    private LocalTime tuesdayOpen;
    @Column(name = "tuesday_close")
    private LocalTime tuesdayClose;

    @Column(name = "wednesday_open")
    private LocalTime wednesdayOpen;
    @Column(name = "wednesday_close")
    private LocalTime wednesdayClose;

    @Column(name = "thursday_open")
    private LocalTime thursdayOpen;
    @Column(name = "thursday_close")
    private LocalTime thursdayClose;

    @Column(name = "friday_open")
    private LocalTime fridayOpen;
    @Column(name = "friday_close")
    private LocalTime fridayClose;

    @Column(name = "saturday_open")
    private LocalTime saturdayOpen;
    @Column(name = "saturday_close")
    private LocalTime saturdayClose;

    @Column(name = "sunday_open")
    private LocalTime sundayOpen;
    @Column(name = "sunday_close")
    private LocalTime sundayClose;

    @Builder
    public StoreHours(Store store, LocalTime mondayOpen, LocalTime mondayClose, LocalTime tuesdayOpen, LocalTime tuesdayClose, LocalTime wednesdayOpen, LocalTime wednesdayClose, LocalTime thursdayOpen, LocalTime thursdayClose, LocalTime fridayOpen, LocalTime fridayClose, LocalTime saturdayOpen, LocalTime saturdayClose, LocalTime sundayOpen, LocalTime sundayClose) {
        this.store = store;
        this.mondayOpen = mondayOpen;
        this.mondayClose = mondayClose;
        this.tuesdayOpen = tuesdayOpen;
        this.tuesdayClose = tuesdayClose;
        this.wednesdayOpen = wednesdayOpen;
        this.wednesdayClose = wednesdayClose;
        this.thursdayOpen = thursdayOpen;
        this.thursdayClose = thursdayClose;
        this.fridayOpen = fridayOpen;
        this.fridayClose = fridayClose;
        this.saturdayOpen = saturdayOpen;
        this.saturdayClose = saturdayClose;
        this.sundayOpen = sundayOpen;
        this.sundayClose = sundayClose;
    }
}
